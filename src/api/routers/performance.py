"""Performance monitoring endpoints for API health and metrics."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from ...auth import get_current_active_user, get_current_user
from ...core.enhanced_config import get_config_manager
from ...core.enhanced_logging import get_loggers
from ...database.models import User
from ..middleware.performance_monitoring import (
    get_performance_middleware,
    get_query_monitor,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint - PUBLIC (no auth required for monitoring)."""
    try:
        config_manager = get_config_manager()
        validation_results = config_manager.validate_configuration()

        return {
            "status": "healthy" if validation_results["valid"] else "unhealthy",
            "environment": validation_results["environment"],
            "errors": validation_results["errors"],
            "warnings": validation_results["warnings"],
            "timestamp": "2024-01-01T00:00:00Z",  # This would be actual timestamp
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service health check failed",
        )


@router.get("/metrics")
async def get_performance_metrics(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get comprehensive performance metrics - AUTHENTICATED USER REQUIRED."""
    try:
        performance_middleware = get_performance_middleware()
        query_monitor = get_query_monitor()
        loggers = get_loggers()

        # Get system metrics
        import psutil

        system_metrics = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "load_average": (
                psutil.getloadavg() if hasattr(psutil, "getloadavg") else None
            ),
        }

        # Get application metrics
        app_metrics = (
            performance_middleware.get_performance_stats()
            if performance_middleware
            else {}
        )
        db_metrics = query_monitor.get_query_stats()

        # Get error statistics
        error_stats = loggers["errors"].get_error_stats()

        logger.info(f"Performance metrics accessed by user: {current_user.username}")

        return {
            "system": system_metrics,
            "application": app_metrics,
            "database": db_metrics,
            "errors": error_stats,
            "timestamp": "2024-01-01T00:00:00Z",  # This would be actual timestamp
        }

    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance metrics",
        )


@router.get("/config")
async def get_configuration_summary(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get configuration summary - AUTHENTICATED USER REQUIRED."""
    try:
        config_manager = get_config_manager()
        logger.info(f"Configuration summary accessed by user: {current_user.username}")
        return config_manager.get_environment_summary()

    except Exception as e:
        logger.error(f"Failed to get configuration summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve configuration summary",
        )


@router.post("/reset-metrics")
async def reset_performance_metrics(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, str]:
    """Reset performance metrics - AUTHENTICATED USER REQUIRED."""
    try:
        # In a real implementation, this would require admin authentication
        performance_middleware = get_performance_middleware()
        query_monitor = get_query_monitor()

        if performance_middleware:
            # Reset middleware metrics
            performance_middleware.request_count = 0
            performance_middleware.total_response_time = 0.0
            performance_middleware.slow_requests = 0

        # Reset query monitor metrics
        query_monitor.query_count = 0
        query_monitor.total_query_time = 0.0
        query_monitor.slow_queries = 0

        logger.info(f"Performance metrics reset by user: {current_user.username}")
        return {
            "status": "success",
            "message": "Performance metrics reset successfully",
        }

    except Exception as e:
        logger.error(f"Failed to reset performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset performance metrics",
        )
