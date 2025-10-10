"""Plugin Management API Router

Provides REST API endpoints for managing plugins including discovery,
loading, configuration, and status monitoring.
"""

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.auth import get_current_user
from src.core.plugin_system import PluginConfig, plugin_manager
from src.database.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plugins", tags=["Plugin Management"])


class PluginConfigRequest(BaseModel):
    """Plugin configuration request."""

    enabled: bool = Field(default=True, description="Whether the plugin is enabled")
    settings: dict[str, Any] = Field(default_factory=dict, description="Plugin-specific settings")
    priority: int = Field(default=100, description="Plugin priority (lower = higher priority)")
    auto_load: bool = Field(default=True, description="Whether to auto-load on startup")


class PluginStatusResponse(BaseModel):
    """Plugin status response."""

    name: str
    discovered: bool
    loaded: bool
    enabled: bool
    metadata: dict[str, Any] | None = None
    config: dict[str, Any] | None = None
    extension_points: list[str] = Field(default_factory=list)


class PluginDiscoveryResponse(BaseModel):
    """Plugin discovery response."""

    total_discovered: int
    plugins: list[dict[str, Any]]
    discovery_paths: list[str]


@router.get("/discover")
async def discover_plugins(
    current_user: User = Depends(get_current_user),
) -> PluginDiscoveryResponse:
    """Discover available plugins in the configured directories.

    This endpoint scans the plugin directories and returns information about
    all discoverable plugins, including their metadata and capabilities.
    """
    try:
        logger.info("User %s requested plugin discovery", current_user.username)

        # Discover plugins
        discovered_plugins = plugin_manager.discover_plugins()

        # Convert metadata to dict format
        plugins_data = []
        for metadata in discovered_plugins:
            plugins_data.append({
                "name": metadata.name,
                "version": metadata.version,
                "description": metadata.description,
                "author": metadata.author,
                "license": metadata.license,
                "capabilities": metadata.capabilities,
                "extension_points": metadata.extension_points,
                "min_system_version": metadata.min_system_version,
                "dependencies": metadata.dependencies,
            })

        return PluginDiscoveryResponse(
            total_discovered=len(discovered_plugins),
            plugins=plugins_data,
            discovery_paths=[str(path) for path in plugin_manager.plugin_directories],
        )

    except (FileNotFoundError, PermissionError, OSError, IOError) as e:
        logger.exception("Plugin discovery failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Plugin discovery failed: {e!s}",
        ) from e


@router.get("/")
async def list_plugins(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """List all plugins with their current status.

    Returns comprehensive information about all discovered and loaded plugins,
    including their configuration and current state.
    """
    try:
        logger.info("User %s requested plugin list", current_user.username)

        # Get all plugin statuses
        plugin_statuses = []
        for plugin_name in plugin_manager.plugin_metadata:
            status_info = plugin_manager.get_plugin_status(plugin_name)
            plugin_statuses.append(status_info)

        # Get loaded plugins summary
        loaded_plugins = plugin_manager.get_loaded_plugins()

        return {
            "total_plugins": len(plugin_manager.plugin_metadata),
            "loaded_plugins": len(plugin_manager.loaded_plugins),
            "extension_points": len(plugin_manager.extension_points),
            "plugins": plugin_statuses,
            "loaded_plugin_names": list(loaded_plugins.keys()),
        }

    except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
        logger.exception("Failed to list plugins: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list plugins: {e!s}",
        ) from e


@router.get("/{plugin_name}")
async def get_plugin_status(
    plugin_name: str,
    current_user: User = Depends(get_current_user),
) -> PluginStatusResponse:
    """Get detailed status information for a specific plugin.

    Args:
        plugin_name: Name of the plugin to get status for

    """
    try:
        logger.info("User %s requested status for plugin: {plugin_name}", current_user.username)

        status_info = plugin_manager.get_plugin_status(plugin_name)

        if not status_info["discovered"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{plugin_name}' not found",
            )

        # Convert metadata to dict if present
        metadata_dict = None
        if status_info["metadata"]:
            metadata = status_info["metadata"]
            metadata_dict = {
                "name": metadata.name,
                "version": metadata.version,
                "description": metadata.description,
                "author": metadata.author,
                "license": metadata.license,
                "capabilities": metadata.capabilities,
                "extension_points": metadata.extension_points,
            }

        # Convert config to dict if present
        config_dict = None
        if status_info["config"]:
            config = status_info["config"]
            config_dict = {
                "enabled": config.enabled,
                "settings": config.settings,
                "priority": config.priority,
                "auto_load": config.auto_load,
                "security_approved": config.security_approved,
            }

        return PluginStatusResponse(
            name=status_info["name"],
            discovered=status_info["discovered"],
            loaded=status_info["loaded"],
            enabled=status_info["enabled"],
            metadata=metadata_dict,
            config=config_dict,
            extension_points=status_info["extension_points"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get plugin status for %s: {e}", plugin_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plugin status: {e!s}",
        ) from e


@router.post("/{plugin_name}/load")
async def load_plugin(
    plugin_name: str,
    config: PluginConfigRequest | None = None,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Load a specific plugin with optional configuration.

    Args:
        plugin_name: Name of the plugin to load
        config: Optional configuration for the plugin

    """
    # Require admin privileges for plugin management
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for plugin management",
        )

    try:
        logger.info("Admin %s requested to load plugin: {plugin_name}", current_user.username)

        # Create plugin config if provided
        plugin_config = None
        if config:
            plugin_config = PluginConfig(
                enabled=config.enabled,
                settings=config.settings,
                priority=config.priority,
                auto_load=config.auto_load,
            )

        # Load the plugin
        success = plugin_manager.load_plugin(plugin_name, plugin_config)

        if success:
            logger.info("Successfully loaded plugin: %s", plugin_name)
            return {
                "success": True,
                "message": f"Plugin '{plugin_name}' loaded successfully",
                "plugin_name": plugin_name,
                "loaded_at": plugin_manager.get_plugin_status(plugin_name),
            }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to load plugin '{plugin_name}'",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to load plugin %s: {e}", plugin_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load plugin: {e!s}",
        ) from e


@router.post("/{plugin_name}/unload")
async def unload_plugin(
    plugin_name: str,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Unload a specific plugin.

    Args:
        plugin_name: Name of the plugin to unload

    """
    # Require admin privileges for plugin management
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for plugin management",
        )

    try:
        logger.info("Admin %s requested to unload plugin: {plugin_name}", current_user.username)

        # Unload the plugin
        success = plugin_manager.unload_plugin(plugin_name)

        if success:
            logger.info("Successfully unloaded plugin: %s", plugin_name)
            return {
                "success": True,
                "message": f"Plugin '{plugin_name}' unloaded successfully",
                "plugin_name": plugin_name,
            }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to unload plugin '{plugin_name}'",
        )

    except HTTPException:
        raise
    except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
        logger.exception("Failed to unload plugin %s: {e}", plugin_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unload plugin: {e!s}",
        ) from e


@router.post("/load-all")
async def load_all_plugins(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Load all discovered plugins.

    This operation runs in the background to avoid timeout issues.
    """
    # Require admin privileges for plugin management
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for plugin management",
        )

    try:
        logger.info("Admin %s requested to load all plugins", current_user.username)

        # Start background task to load all plugins
        background_tasks.add_task(_load_all_plugins_background)

        return {
            "success": True,
            "message": "Plugin loading started in background",
            "total_plugins": len(plugin_manager.plugin_metadata),
            "status": "loading",
        }

    except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
        logger.exception("Failed to start plugin loading: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start plugin loading: {e!s}",
        ) from e


@router.get("/extension-points")
async def list_extension_points(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """List all available extension points and their handlers.

    Extension points are named interfaces that plugins can implement
    to extend the system's functionality.
    """
    try:
        logger.info("User %s requested extension points list", current_user.username)

        extension_points_info = {}

        for point_name, handlers in plugin_manager.extension_points.items():
            extension_points_info[point_name] = {
                "handler_count": len(handlers),
                "handlers": [
                    {
                        "function_name": handler.__name__ if hasattr(handler, "__name__") else str(handler),
                        "module": handler.__module__ if hasattr(handler, "__module__") else "unknown",
                    }
                    for handler in handlers
                ],
            }

        return {
            "total_extension_points": len(plugin_manager.extension_points),
            "extension_points": extension_points_info,
        }

    except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
        logger.exception("Failed to list extension points: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list extension points: {e!s}",
        ) from e


async def _load_all_plugins_background():
    """Background task to load all plugins."""
    try:
        logger.info("Starting background plugin loading")
        results = plugin_manager.load_all_plugins()

        successful_loads = sum(1 for success in results.values() if success)
        total_plugins = len(results)

        logger.info("Background plugin loading complete: %s/{total_plugins} successful", successful_loads)

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.exception("Background plugin loading failed: %s", e)
