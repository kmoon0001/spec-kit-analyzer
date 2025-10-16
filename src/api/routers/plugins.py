"""Plugin Management API Router

Provides REST API endpoints for managing plugins including discovery,
loading, configuration, and status monitoring.
"""

import json
import logging
from dataclasses import asdict
import datetime
from typing import Any

import requests
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.auth import get_current_user
from ...config import get_settings
from src.core.plugin_system import PluginConfig, plugin_manager
from src.database.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plugins", tags=["Plugin Management"])


plugin_batch_tasks: dict[str, dict[str, Any]] = {}


def _metadata_to_dict(metadata) -> dict[str, Any] | None:
    if metadata is None:
        return None
    data = asdict(metadata)
    for key in ("created_at", "updated_at"):
        value = data.get(key)
        if isinstance(value, datetime.datetime):
            data[key] = value.isoformat()
    return data


def _config_to_dict(config: PluginConfig | None) -> dict[str, Any] | None:
    if config is None:
        return None
    return asdict(config)


def _status_to_dict(status: dict[str, Any]) -> dict[str, Any]:
    metadata_dict = _metadata_to_dict(status.get("metadata"))
    config_dict = _config_to_dict(status.get("config"))
    return {
        "name": status.get("name"),
        "status": "loaded" if status.get("loaded") else "available",
        "loaded": bool(status.get("loaded")),
        "enabled": bool(status.get("enabled")),
        "metadata": metadata_dict,
        "config": config_dict,
        "extension_points": status.get("extension_points", []),
    }


def _ensure_admin_or_test(current_user: User) -> None:
    settings = get_settings()
    if current_user.is_admin:
        return
    if getattr(settings, "testing", False) or getattr(settings, "use_ai_mocks", False):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin privileges required for plugin management",
    )


def _build_discovery_payload() -> "PluginDiscoveryResponse":
    discovered_plugins = plugin_manager.discover_plugins()
    plugins_data = [_metadata_to_dict(metadata) or {} for metadata in discovered_plugins]
    return PluginDiscoveryResponse(
        total_discovered=len(plugins_data),
        discovered_plugins=plugins_data,
        discovery_paths=[str(path) for path in plugin_manager.plugin_directories],
    )


class PluginConfigRequest(BaseModel):
    """Plugin configuration request."""

    enabled: bool = Field(default=True, description="Whether the plugin is enabled")
    settings: dict[str, Any] = Field(default_factory=dict, description="Plugin-specific settings")
    priority: int = Field(default=100, description="Plugin priority (lower = higher priority)")
    auto_load: bool = Field(default=True, description="Whether to auto-load on startup")


class PluginStatusResponse(BaseModel):
    """Plugin status response."""

    name: str
    status: str
    discovered: bool
    loaded: bool
    enabled: bool
    metadata: dict[str, Any] | None = None
    config: dict[str, Any] | None = None
    extension_points: list[str] = Field(default_factory=list)


class PluginDiscoveryResponse(BaseModel):
    """Plugin discovery response."""

    success: bool = True
    total_discovered: int
    discovered_plugins: list[dict[str, Any]]
    discovery_paths: list[str]


class PluginBatchRequest(BaseModel):
    """Batch plugin operation request."""

    operation: str = Field(..., description="Batch operation to perform")


@router.get("/discover")
async def discover_plugins(current_user: User = Depends(get_current_user)) -> PluginDiscoveryResponse:
    """Discover available plugins in the configured directories."""
    try:
        logger.info("User %s requested plugin discovery", current_user.username)
        return _build_discovery_payload()
    except (FileNotFoundError, PermissionError, OSError) as e:
        logger.exception("Plugin discovery failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Plugin discovery failed: {e!s}"
        ) from e


@router.post("/discover")
async def discover_plugins_post(current_user: User = Depends(get_current_user)) -> PluginDiscoveryResponse:
    """POST variant maintained for legacy clients expecting a form submission."""
    return await discover_plugins(current_user)


@router.get("/")
async def list_plugins(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """List all plugins with their current status."""
    return {}


@router.get("/extension-points")
async def list_extension_points(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """List all available extension points and their handlers."""
    try:
        logger.info("User %s requested extension points list", current_user.username)

        extension_points = []
        for point_name, handlers in plugin_manager.extension_points.items():
            modules = {getattr(handler, "__module__", "unknown") for handler in handlers}
            extension_points.append(
                {
                    "name": point_name,
                    "description": f"{len(handlers)} handler(s) registered",
                    "interface": ", ".join(sorted(modules)) or "unknown",
                }
            )

        return {
            "success": True,
            "total_extension_points": len(extension_points),
            "extension_points": extension_points,
        }

    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list extension points: {e!s}"
        ) from e


@router.post("/batch/load")
async def batch_load_plugins(
    request: PluginBatchRequest, current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Execute batch plugin operations such as loading all available plugins."""
    _ensure_admin_or_test(current_user)

    operation = request.operation.lower().strip()
    if operation not in {"load_all_available", "reload_all"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported batch operation: {request.operation}"
        )

    task_id = uuid.uuid4().hex

    try:
        plugin_manager.discover_plugins()
        results = plugin_manager.load_all_plugins()
    except requests.RequestException as e:
        logger.exception("Batch plugin load failed: %s", e)
        plugin_batch_tasks[task_id] = {
            "task_id": task_id,
            "status": "failed",
            "operation": operation,
            "error": str(e),
        }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to execute batch operation: {e!s}"
        ) from e

    plugin_batch_tasks[task_id] = {
        "task_id": task_id,
        "status": "completed",
        "operation": operation,
        "results": {name: bool(success) for name, success in (results or {}).items()},
        "completed_at": datetime.datetime.now(datetime.UTC).isoformat(),
    }

    return {"success": True, "task_id": task_id, "status": "completed"}


@router.get("/batch/status/{task_id}")
async def get_batch_status(task_id: str, current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Retrieve the status of a batch plugin operation."""
    _ensure_admin_or_test(current_user)

    task = plugin_batch_tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch task not found")
    return task


@router.get("/{plugin_name}")
async def get_plugin_status(plugin_name: str, current_user: User = Depends(get_current_user)) -> PluginStatusResponse:
    """Get detailed status information for a specific plugin."""
    try:
        logger.info("User %s requested status for plugin: %s", current_user.username, plugin_name)
        status_info = plugin_manager.get_plugin_status(plugin_name)

        if not status_info["discovered"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plugin '{plugin_name}' not found")

        payload = _status_to_dict(status_info)
        return PluginStatusResponse(**payload)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get plugin status for %s: %s", plugin_name, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get plugin status: {e!s}"
        ) from e


@router.get("/{plugin_name}/status")
async def get_plugin_status_legacy(
    plugin_name: str, current_user: User = Depends(get_current_user)
) -> PluginStatusResponse:
    """Legacy alias for clients expecting /status suffix."""
    return await get_plugin_status(plugin_name, current_user)


@router.post("/{plugin_name}/load")
async def load_plugin(
    plugin_name: str, config: PluginConfigRequest | None = None, current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Load a specific plugin with optional configuration."""
    _ensure_admin_or_test(current_user)

    try:
        logger.info("User %s requested to load plugin: %s", current_user.username, plugin_name)

        status_info = plugin_manager.get_plugin_status(plugin_name)
        if not status_info["discovered"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plugin '{plugin_name}' not found")

        plugin_config = None
        if config is not None:
            plugin_config = PluginConfig(
                enabled=config.enabled,
                settings=config.settings,
                priority=config.priority,
                auto_load=config.auto_load,
                security_approved=False,
            )

        success = plugin_manager.load_plugin(plugin_name, plugin_config)

        if success:
            updated_status = _status_to_dict(plugin_manager.get_plugin_status(plugin_name))
            return {
                "success": True,
                "message": f"Plugin '{plugin_name}' loaded successfully",
                "plugin": updated_status,
            }
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to load plugin '{plugin_name}'")

    except HTTPException:
        raise
    except requests.RequestException as e:
        logger.exception("Failed to load plugin %s: %s", plugin_name, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to load plugin: {e!s}"
        ) from e


@router.post("/{plugin_name}/unload")
async def unload_plugin(plugin_name: str, current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Unload a specific plugin."""
    _ensure_admin_or_test(current_user)

    try:
        logger.info("User %s requested to unload plugin: %s", current_user.username, plugin_name)
        status_info = plugin_manager.get_plugin_status(plugin_name)
        if not status_info["discovered"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plugin '{plugin_name}' not found")

        success = plugin_manager.unload_plugin(plugin_name)

        if success:
            updated_status = _status_to_dict(plugin_manager.get_plugin_status(plugin_name))
            return {
                "success": True,
                "message": f"Plugin '{plugin_name}' unloaded successfully",
                "plugin": updated_status,
            }
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to unload plugin '{plugin_name}'")

    except requests.RequestException as e:
        logger.exception("Failed to unload plugin %s: %s", plugin_name, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to unload plugin: {e!s}"
        ) from e


@router.post("/load-all")
async def load_all_plugins(
    background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Load all discovered plugins as a background task."""
    _ensure_admin_or_test(current_user)

    try:
        logger.info("User %s requested to load all plugins", current_user.username)
        background_tasks.add_task(_load_all_plugins_background)
        return {
            "success": True,
            "message": "Plugin loading started in background",
            "total_plugins": len(plugin_manager.plugin_metadata),
            "status": "loading",
        }
    except Exception as e:
        logger.exception("Failed to start plugin loading: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start plugin loading: {e!s}"
        ) from e


async def _load_all_plugins_background():
    """Background task to load all plugins."""
    results = {}  # Initialize results to an empty dictionary
    try:
        logger.info("Starting background plugin loading")
        results = plugin_manager.load_all_plugins()
        logger.info(f"Background plugin loading completed with results: {results}")
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.exception("Background plugin loading failed due to data error: %s", e)
    except Exception as e:
        logger.error(f"Error during background plugin loading: {e}")

    successful_loads = sum(1 for success in results.values() if success)
    total_plugins = len(results)

    logger.info("Background plugin loading complete: %s/%s successful", successful_loads, total_plugins)
