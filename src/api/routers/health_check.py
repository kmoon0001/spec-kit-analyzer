"""
Comprehensive Health Check System
Provides detailed system health monitoring and diagnostics
"""

import asyncio
import os
import platform
import time
from datetime import UTC, datetime
from typing import Any

import psutil
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import get_current_user
from src.database import get_async_db
from src.database.models import User

logger = structlog.get_logger(__name__)

router = APIRouter()


class HealthStatus(BaseModel):
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    version: str
    uptime_seconds: float


class ComponentHealth(BaseModel):
    name: str
    status: str
    message: str
    response_time_ms: float | None = None
    details: dict[str, Any] | None = None


class SystemMetrics(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    disk_free_gb: float
    load_average: list[float] | None = None


class DetailedHealthResponse(BaseModel):
    overall: HealthStatus
    components: list[ComponentHealth]
    system_metrics: SystemMetrics
    dependencies: dict[str, Any]


# Store startup time for uptime calculation
_startup_time = time.time()


async def check_database_health(db: AsyncSession) -> ComponentHealth:
    """Check database connectivity and performance"""
    start_time = time.time()

    try:
        # Simple query to test connectivity
        result = await db.execute(text("SELECT 1"))
        result.fetchone()

        response_time = (time.time() - start_time) * 1000

        if response_time > 1000:  # > 1 second
            return ComponentHealth(
                name="database",
                status="degraded",
                message=f"Database responding slowly ({response_time:.0f}ms)",
                response_time_ms=response_time,
            )

        return ComponentHealth(
            name="database",
            status="healthy",
            message="Database connection successful",
            response_time_ms=response_time,
        )

    except Exception as e:
        return ComponentHealth(
            name="database",
            status="unhealthy",
            message=f"Database connection failed: {str(e)}",
            response_time_ms=(time.time() - start_time) * 1000,
        )


async def check_ai_services_health() -> ComponentHealth:
    """Check AI services availability"""
    start_time = time.time()

    try:
        # Check if AI services are available
        from src.core.analysis_service import AnalysisService
        from src.core.hybrid_retriever import HybridRetriever

        # Try to initialize services (lightweight check)
        retriever = HybridRetriever()
        analysis_service = AnalysisService(retriever=retriever)

        response_time = (time.time() - start_time) * 1000

        details = {
            "use_mocks": analysis_service.use_mocks,
            "retriever_initialized": (
                retriever.is_initialized
                if hasattr(retriever, "is_initialized")
                else False
            ),
        }

        return ComponentHealth(
            name="ai_services",
            status="healthy",
            message="AI services available",
            response_time_ms=response_time,
            details=details,
        )

    except Exception as e:
        return ComponentHealth(
            name="ai_services",
            status="degraded",
            message=f"AI services partially available: {str(e)}",
            response_time_ms=(time.time() - start_time) * 1000,
        )


async def check_worker_manager_health() -> ComponentHealth:
    """Check worker manager status"""
    try:
        from src.core.worker_manager import get_worker_manager

        worker_manager = get_worker_manager()
        stats = worker_manager.get_stats()

        # Check if worker manager is healthy
        active_workers = stats.get("active_workers", 0)
        max_workers = stats.get("max_workers", 0)
        queue_size = stats.get("queue_size", 0)

        if queue_size > max_workers * 2:  # Queue is getting large
            status = "degraded"
            message = f"Worker queue is large ({queue_size} tasks)"
        else:
            status = "healthy"
            message = f"Worker manager operational ({active_workers}/{max_workers} workers active)"

        return ComponentHealth(
            name="worker_manager", status=status, message=message, details=stats
        )

    except Exception as e:
        return ComponentHealth(
            name="worker_manager",
            status="unhealthy",
            message=f"Worker manager unavailable: {str(e)}",
        )


def get_system_metrics() -> SystemMetrics:
    """Get current system metrics"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)

        # Disk usage
        disk = psutil.disk_usage("/")
        disk_usage_percent = (disk.used / disk.total) * 100
        disk_free_gb = disk.free / (1024**3)

        # Load average (Unix only)
        load_average = None
        if hasattr(os, "getloadavg"):
            load_average = list(os.getloadavg())

        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_gb=memory_available_gb,
            disk_usage_percent=disk_usage_percent,
            disk_free_gb=disk_free_gb,
            load_average=load_average,
        )

    except Exception as e:
        logger.exception("Failed to get system metrics", error=str(e))
        # Return default values if metrics collection fails
        return SystemMetrics(
            cpu_percent=0.0,
            memory_percent=0.0,
            memory_available_gb=0.0,
            disk_usage_percent=0.0,
            disk_free_gb=0.0,
        )


def get_dependencies_info() -> dict[str, Any]:
    """Get information about system dependencies"""
    try:
        import sys

        import pkg_resources

        # Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        # Key package versions
        key_packages = [
            "fastapi",
            "uvicorn",
            "sqlalchemy",
            "pydantic",
            "torch",
            "transformers",
            "sentence-transformers",
            "presidio-analyzer",
            "presidio-anonymizer",
        ]

        package_versions = {}
        for package in key_packages:
            try:
                version = pkg_resources.get_distribution(package).version
                package_versions[package] = version
            except pkg_resources.DistributionNotFound:
                package_versions[package] = "not installed"

        return {
            "python_version": python_version,
            "platform": platform.platform(),
            "architecture": platform.architecture()[0],
            "packages": package_versions,
        }

    except Exception as e:
        logger.exception("Failed to get dependencies info", error=str(e))
        return {"error": str(e)}


@router.get("/health", response_model=HealthStatus)
async def basic_health_check():
    """Basic health check endpoint"""
    uptime = time.time() - _startup_time

    return HealthStatus(
        status="healthy",
        timestamp=datetime.now(UTC),
        version="1.0.0",  # This should come from your app version
        uptime_seconds=uptime,
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Detailed health check with component status"""

    # Check all components
    components = await asyncio.gather(
        check_database_health(db),
        check_ai_services_health(),
        check_worker_manager_health(),
        return_exceptions=True,
    )

    # Handle any exceptions in component checks
    valid_components = []
    for i, component in enumerate(components):
        if isinstance(component, Exception):
            component_names = ["database", "ai_services", "worker_manager"]
            valid_components.append(
                ComponentHealth(
                    name=(
                        component_names[i]
                        if i < len(component_names)
                        else f"component_{i}"
                    ),
                    status="unhealthy",
                    message=f"Health check failed: {str(component)}",
                )
            )
        elif isinstance(component, ComponentHealth):
            valid_components.append(component)
        else:
            # Handle unexpected types
            valid_components.append(
                ComponentHealth(
                    name=f"component_{i}",
                    status="unknown",
                    message=f"Unexpected component type: {type(component)}",
                )
            )

    # Determine overall status
    unhealthy_count = sum(1 for c in valid_components if c.status == "unhealthy")
    degraded_count = sum(1 for c in valid_components if c.status == "degraded")

    if unhealthy_count > 0:
        overall_status = "unhealthy"
    elif degraded_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    # Get system metrics
    system_metrics = get_system_metrics()

    # Get dependencies info
    dependencies = get_dependencies_info()

    uptime = time.time() - _startup_time

    return DetailedHealthResponse(
        overall=HealthStatus(
            status=overall_status,
            timestamp=datetime.now(UTC),
            version="1.0.0",
            uptime_seconds=uptime,
        ),
        components=valid_components,
        system_metrics=system_metrics,
        dependencies=dependencies,
    )


@router.get("/health/readiness")
async def readiness_check(db: AsyncSession = Depends(get_async_db)):
    """Kubernetes-style readiness probe"""
    try:
        # Check database connectivity
        await db.execute(text("SELECT 1"))

        # Check if critical services are available

        return {"status": "ready", "timestamp": datetime.now(UTC)}

    except Exception as e:
        logger.exception("Readiness check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}",
        ) from e


@router.get("/health/liveness")
async def liveness_check():
    """Kubernetes-style liveness probe"""
    # Simple check that the application is running
    return {
        "status": "alive",
        "timestamp": datetime.now(UTC),
        "uptime_seconds": time.time() - _startup_time,
    }


@router.get("/health/metrics")
async def metrics_endpoint(current_user: User = Depends(get_current_user)):
    """Prometheus-style metrics endpoint"""

    # Get system metrics
    metrics = get_system_metrics()

    # Get worker manager stats
    try:
        from src.core.worker_manager import get_worker_manager

        worker_stats = get_worker_manager().get_stats()
    except Exception:
        worker_stats = {}

    uptime = time.time() - _startup_time

    # Format as Prometheus metrics
    prometheus_metrics = f"""
# HELP app_uptime_seconds Application uptime in seconds
# TYPE app_uptime_seconds counter
app_uptime_seconds {uptime}

# HELP system_cpu_percent CPU usage percentage
# TYPE system_cpu_percent gauge
system_cpu_percent {metrics.cpu_percent}

# HELP system_memory_percent Memory usage percentage
# TYPE system_memory_percent gauge
system_memory_percent {metrics.memory_percent}

# HELP system_disk_usage_percent Disk usage percentage
# TYPE system_disk_usage_percent gauge
system_disk_usage_percent {metrics.disk_usage_percent}

# HELP worker_active_count Active worker threads
# TYPE worker_active_count gauge
worker_active_count {worker_stats.get('active_workers', 0)}

# HELP worker_queue_size Worker queue size
# TYPE worker_queue_size gauge
worker_queue_size {worker_stats.get('queue_size', 0)}

# HELP worker_total_tasks Total tasks processed
# TYPE worker_total_tasks counter
worker_total_tasks {worker_stats.get('total_tasks', 0)}
""".strip()

    return {"metrics": prometheus_metrics}


# Add health check routes to the main router
def setup_health_routes(app):
    """Setup health check routes on the main app"""
    app.include_router(router, prefix="/health", tags=["Health"])
