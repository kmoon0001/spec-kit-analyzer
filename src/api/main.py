"""
Clinical Compliance Analyzer API

FastAPI backend for the Therapy Compliance Analyzer desktop application.
Provides endpoints for document analysis, user management, and compliance reporting.
"""

import os
import shutil
import structlog
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.dependencies import (
    shutdown_event as api_shutdown,
    startup_event as api_startup,
)
from src.api.routers import admin, analysis, auth, chat, compliance, dashboard, health
from src.api.global_exception_handler import global_exception_handler, http_exception_handler
from src.core.database_maintenance_service import DatabaseMaintenanceService
from src.config import get_settings
from src.logging_config import CorrelationIdMiddleware

settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])

# --- Configuration ---
DATABASE_PURGE_RETENTION_DAYS = settings.maintenance.purge_retention_days

# --- Logging ---
logger = structlog.get_logger(__name__)


# --- Helper Functions ---
def clear_temp_uploads():
    """Clears all files from the temporary upload directory."""
    directory_path = settings.paths.temp_upload_dir
    try:
        if os.path.exists(directory_path):
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    logger.info("Successfully cleaned up temporary file", file_path=file_path)
                except (OSError, PermissionError) as e:
                    logger.error("Failed to delete temp file", file_path=file_path, error=str(e))
    except Exception as e:
        logger.exception("An unexpected error occurred while clearing temp uploads", error=str(e))


def run_database_maintenance():
    """
    Instantiates and runs the database maintenance service.
    Includes error handling to prevent scheduler crashes.
    """
    logger.info("Scheduler triggered: Starting database maintenance job.")
    try:
        maintenance_service = DatabaseMaintenanceService()
        maintenance_service.purge_old_reports(
            retention_days=DATABASE_PURGE_RETENTION_DAYS
        )
        logger.info("Scheduler job: Database maintenance finished.")
    except Exception as e:
        logger.exception("Database maintenance job failed", error=str(e))


# --- FastAPI App Setup ---
scheduler = BackgroundScheduler(daemon=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    # 1. Run API-level startup logic (e.g., model loading)
    await api_startup()

    # 2. Clean up any orphaned temporary files from previous runs.
    logger.info("Clearing temporary upload directory...")
    try:
        clear_temp_uploads()
    except Exception as e:
        logger.error("An error occurred during temp file cleanup", error=str(e))

    # 3. Initialize and start the background scheduler
    scheduler.add_job(run_database_maintenance, "interval", days=1)
    scheduler.start()
    logger.info("Scheduler started for daily database maintenance.")

    yield

    # Shutdown
    await api_shutdown()
    scheduler.shutdown()  # Ensure scheduler is shut down gracefully


app = FastAPI(
    title="Clinical Compliance Analyzer API",
    description="API for analyzing clinical documents for compliance.",
    version="1.0.0",
    lifespan=lifespan,
)


# --- Middleware and Exception Handlers ---
app.add_middleware(CorrelationIdMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# --- Routers ---
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(analysis.router, tags=["Analysis"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(compliance.router, tags=["Compliance"])


@app.get("/")
def read_root():
    """Root endpoint providing API welcome message."""
    return {"message": "Welcome to the Clinical Compliance Analyzer API"}