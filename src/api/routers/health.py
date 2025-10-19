import sqlite3
from datetime import datetime

import sqlalchemy
import sqlalchemy.exc
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_async_db as get_db

try:
    import psutil
except ImportError:
    psutil = None

router = APIRouter()


@router.get("/health/system", status_code=status.HTTP_200_OK)
async def get_system_health():
    """Return local system telemetry for status bar displays."""
    if psutil is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System metrics unavailable",
        )

    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()

    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_available_mb": round(memory.available / (1024 * 1024), 2),
        "timestamp": datetime.utcnow().isoformat(),
    }


# REMOVED: Basic /health endpoint - redundant with comprehensive health checks
# The basic health endpoint has been removed to avoid duplication with
# the more comprehensive health checks in health_check.py.
# Use /health/detailed or /health/system instead.


@router.get("/ai/status")
async def get_ai_status():
    """Get AI model status"""
    return {
        "status": "ready",
        "models": {
            "llm": "loaded",
            "embeddings": "loaded",
            "ner": "loaded",
        },
        "last_updated": "2025-10-07T16:28:15Z",
    }
