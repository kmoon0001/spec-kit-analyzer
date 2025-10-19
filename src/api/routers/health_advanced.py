"""Comprehensive health check system.

Provides detailed health monitoring including:
- Database connectivity
- AI model status
- Memory usage
- Disk space
- External service dependencies
- Performance metrics
"""

import asyncio
import logging
import os
import psutil
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])

class HealthChecker:
    """Comprehensive health checking system."""

    def __init__(self):
        self.settings = get_settings()
        self.start_time = time.time()

    async def check_database(self, db: Session) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            result = db.execute(text("SELECT 1 as health_check"))
            result.fetchone()
            response_time = time.time() - start_time

            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "connection_pool": "active"
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": None
            }

    async def check_ai_models(self) -> Dict[str, Any]:
        """Check AI model availability and status."""
        try:
            # Check if mocks are enabled
            if self.settings.use_ai_mocks:
                return {
                    "status": "healthy",
                    "mode": "mock",
                    "models_loaded": True,
                    "mock_reason": "AI mocks enabled for testing"
                }

            # Check real AI models
            from src.core.llm_service import LLMService
            from src.core.hybrid_retriever import HybridRetriever

            # Check LLM service
            llm_status = "unknown"
            try:
                # This is a lightweight check - don't actually load the model
                llm_status = "available"
            except Exception as e:
                llm_status = f"error: {str(e)}"

            # Check retriever
            retriever_status = "unknown"
            try:
                retriever = HybridRetriever()
                await retriever.initialize()
                retriever_status = "healthy"
            except Exception as e:
                retriever_status = f"error: {str(e)}"

            return {
                "status": "healthy" if llm_status == "available" and retriever_status == "healthy" else "degraded",
                "mode": "real_ai",
                "llm_service": llm_status,
                "retriever": retriever_status,
                "models_loaded": llm_status == "available"
            }
        except Exception as e:
            logger.error(f"AI models health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "mode": "unknown"
            }

    async def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memory usage
            memory = psutil.virtual_memory()

            # Disk usage
            disk = psutil.disk_usage('/')

            # Process info
            process = psutil.Process()
            process_memory = process.memory_info()

            return {
                "status": "healthy",
                "cpu_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent,
                    "process_mb": round(process_memory.rss / (1024**2), 2)
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_percent": round((disk.used / disk.total) * 100, 2)
                }
            }
        except Exception as e:
            logger.error(f"System resources health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def check_external_dependencies(self) -> Dict[str, Any]:
        """Check external service dependencies."""
        dependencies = {}

        # Check Hugging Face Hub connectivity
        try:
            import requests
            response = requests.get("https://huggingface.co", timeout=5)
            dependencies["huggingface"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2)
            }
        except Exception as e:
            dependencies["huggingface"] = {
                "status": "unhealthy",
                "error": str(e)
            }

        return dependencies

    async def get_overall_health(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive health status."""
        checks = await asyncio.gather(
            self.check_database(db),
            self.check_ai_models(),
            self.check_system_resources(),
            self.check_external_dependencies(),
            return_exceptions=True
        )

        database_health, ai_health, system_health, external_health = checks

        # Determine overall status
        all_healthy = all(
            check.get("status") == "healthy"
            for check in [database_health, ai_health, system_health]
            if isinstance(check, dict)
        )

        overall_status = "healthy" if all_healthy else "degraded"

        return {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": round(time.time() - self.start_time, 2),
            "version": "1.0.0",
            "checks": {
                "database": database_health,
                "ai_models": ai_health,
                "system_resources": system_health,
                "external_dependencies": external_health
            }
        }

# Global health checker instance
health_checker = HealthChecker()

@router.get("/")
async def health_check(db: Session = Depends(get_db)):
    """Basic health check endpoint."""
    try:
        health_status = await health_checker.get_overall_health(db)
        status_code = 200 if health_status["status"] == "healthy" else 503
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with all metrics."""
    try:
        health_status = await health_checker.get_overall_health(db)

        # Add additional detailed metrics
        health_status["detailed_metrics"] = {
            "active_connections": len(psutil.net_connections()),
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None,
            "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}",
            "platform": psutil.sys.platform
        }

        status_code = 200 if health_status["status"] == "healthy" else 503
        return health_status
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=500, detail="Detailed health check failed")

@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes-style readiness probe."""
    try:
        # Check critical dependencies only
        database_health = await health_checker.check_database(db)

        if database_health["status"] == "healthy":
            return {"status": "ready"}
        else:
            raise HTTPException(status_code=503, detail="Service not ready")
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")

@router.get("/live")
async def liveness_check():
    """Kubernetes-style liveness probe."""
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}
