"""Cleanup API endpoints for manual cleanup operations."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from src.api.deps.request_tracking import RequestId, log_with_request_id
from src.auth import get_current_active_user
from src.core.cleanup_services import CleanupManager, cleanup_manager
from src.database.models import User

router = APIRouter(prefix="/cleanup", tags=["Cleanup"])


def get_cleanup_manager() -> CleanupManager:
    """Get the cleanup manager instance."""
    return cleanup_manager


@router.get("/health")
async def get_cleanup_health(
    cleanup_mgr: CleanupManager = Depends(get_cleanup_manager),
    request_id: str = RequestId,
    current_user: User = Depends(get_current_active_user),
) -> JSONResponse:
    """Get health status of all cleanup services."""
    log_with_request_id(
        request_id, f"Cleanup health check requested by user {current_user.id}"
    )

    try:
        health_status = await cleanup_mgr.health_check_all()

        return JSONResponse(
            content={
                "status": "success",
                "data": health_status,
                "request_id": request_id,
            }
        )
    except Exception as e:
        log_with_request_id(request_id, f"Cleanup health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")


@router.get("/stats")
async def get_cleanup_stats(
    cleanup_mgr: CleanupManager = Depends(get_cleanup_manager),
    request_id: str = RequestId,
    current_user: User = Depends(get_current_active_user),
) -> JSONResponse:
    """Get statistics for all cleanup services."""
    log_with_request_id(
        request_id, f"Cleanup stats requested by user {current_user.id}"
    )

    try:
        stats = cleanup_mgr.get_service_stats()

        return JSONResponse(
            content={"status": "success", "data": stats, "request_id": request_id}
        )
    except Exception as e:
        log_with_request_id(request_id, f"Cleanup stats failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {e}")


@router.post("/run")
async def run_cleanup_now(
    service_name: Optional[str] = None,
    cleanup_mgr: CleanupManager = Depends(get_cleanup_manager),
    request_id: str = RequestId,
    current_user: User = Depends(get_current_active_user),
) -> JSONResponse:
    """Run cleanup immediately for specified service or all services."""
    log_with_request_id(
        request_id,
        f"Manual cleanup requested by user {current_user.id} for service: {service_name}",
    )

    try:
        results = await cleanup_mgr.run_cleanup_now(service_name)

        return JSONResponse(
            content={"status": "success", "data": results, "request_id": request_id}
        )
    except Exception as e:
        log_with_request_id(request_id, f"Manual cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {e}")


@router.post("/start")
async def start_cleanup_services(
    cleanup_mgr: CleanupManager = Depends(get_cleanup_manager),
    request_id: str = RequestId,
    current_user: User = Depends(get_current_active_user),
) -> JSONResponse:
    """Start all cleanup services."""
    log_with_request_id(
        request_id, f"Start cleanup services requested by user {current_user.id}"
    )

    try:
        await cleanup_mgr.start_all()

        return JSONResponse(
            content={
                "status": "success",
                "message": "All cleanup services started",
                "request_id": request_id,
            }
        )
    except Exception as e:
        log_with_request_id(request_id, f"Start cleanup services failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start cleanup services: {e}"
        )


@router.post("/stop")
async def stop_cleanup_services(
    cleanup_mgr: CleanupManager = Depends(get_cleanup_manager),
    request_id: str = RequestId,
    current_user: User = Depends(get_current_active_user),
) -> JSONResponse:
    """Stop all cleanup services."""
    log_with_request_id(
        request_id, f"Stop cleanup services requested by user {current_user.id}"
    )

    try:
        await cleanup_mgr.stop_all()

        return JSONResponse(
            content={
                "status": "success",
                "message": "All cleanup services stopped",
                "request_id": request_id,
            }
        )
    except Exception as e:
        log_with_request_id(request_id, f"Stop cleanup services failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to stop cleanup services: {e}"
        )
