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


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Performs a health check of the API.
    This endpoint can be called by a monitoring service to verify that the
    application is running and can connect to the database.
    """
    try:
        # Perform a simple, fast query to check the database connection
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "error", "database": "disconnected", "reason": str(e)},
        ) from e


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
