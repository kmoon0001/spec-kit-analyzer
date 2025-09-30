"""
Clinical Compliance Analyzer API

FastAPI backend for the Therapy Compliance Analyzer desktop application.
Provides endpoints for document analysis, user management, and compliance reporting.
"""
import os
import shutil
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from logging.config import dictConfig

from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from .dependencies import startup_event as api_startup, shutdown_event as api_shutdown
from .error_handling import http_exception_handler
from .routers import admin, analysis, auth, chat, compliance, dashboard, health, users
from ..config import get_settings
from ..core.database_maintenance_service import DatabaseMaintenanceService

def configure_logging() -> None:
    """Configure structured logging for the API process."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": fmt}
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": log_level,
            }
        },
        "root": {"handlers": ["console"], "level": log_level},
    })

configure_logging()

settings = get_settings()

# --- Configuration ---
DATABASE_PURGE_RETENTION_DAYS = settings.maintenance.purge_retention_days
TEMP_UPLOAD_DIR = settings.temp_upload_dir

# --- Logging ---
logger = logging.getLogger(__name__)


# --- Helper Functions ---

def validate_settings(cfg) -> None:
    """Validate critical settings to avoid unsafe or invalid configuration."""
    try:
        days = int(cfg.maintenance.purge_retention_days)
        if days < 0 or days > 3650:
            raise ValueError("purge_retention_days out of safe range (0..3650)")
    except Exception as exc:
        raise ValueError(f"Invalid purge_retention_days: {exc}") from exc

    temp_dir = os.path.realpath(cfg.temp_upload_dir)
    if not temp_dir or len(temp_dir) < 5:
        raise ValueError("TEMP_UPLOAD_DIR path is suspiciously short/empty")
    drive, tail = os.path.splitdrive(temp_dir)
    if (not tail or tail in (os.path.sep, "/", "\\")) and drive:
        raise ValueError(f"TEMP_UPLOAD_DIR points to drive root: {temp_dir}")
    if temp_dir in {os.path.sep, "/", "C:\\", "D:\\"}:
        raise ValueError(f"TEMP_UPLOAD_DIR points to unsafe path: {temp_dir}")

    # Optionally ensure it exists
    if not os.path.exists(temp_dir):
        try:
            os.makedirs(temp_dir, exist_ok=True)
        except Exception as exc:
            raise ValueError(f"Unable to create TEMP_UPLOAD_DIR '{temp_dir}': {exc}") from exc
def clear_temp_uploads() -> None:
    """Safely clear files from the temporary upload directory.

    Adds guardrails to prevent accidental deletion of unsafe directories.
    """
    try:
        temp_dir = os.path.realpath(TEMP_UPLOAD_DIR)
        if not os.path.isdir(temp_dir):
            logger.warning("Temp upload dir does not exist or is not a directory: %s", temp_dir)
            return

        # Guard against dangerous directories (root, drive root, or suspiciously short paths)
        drive, tail = os.path.splitdrive(temp_dir)
        if (not tail or tail in (os.path.sep, "/", "\\")) and drive:
            logger.error("Refusing to clean drive root: %s", temp_dir)
            return
        if temp_dir in {os.path.sep, "/", "C:\\", "D:\\"} or len(temp_dir) < 5:
            logger.error("Refusing to clean unsafe temp dir: %s", temp_dir)
            return

        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                logger.info("Successfully cleaned up temporary file: %s", file_path)
            except (OSError, PermissionError) as e:
                logger.error("Failed to delete %s. Reason: %s", file_path, e)
    except Exception as e:
        logger.exception("An unexpected error occurred while clearing temp uploads: %s", e)


def run_database_maintenance():
    """
    Instantiates and runs the database maintenance service.
    Includes error handling to prevent scheduler crashes.
    """
    logger.info("Scheduler triggered: Starting database maintenance job.")
    try:
        maintenance_service = DatabaseMaintenanceService()
        maintenance_service.purge_old_reports(retention_days=DATABASE_PURGE_RETENTION_DAYS)
        logger.info("Scheduler job: Database maintenance finished.")
    except Exception as e:
        logger.exception("Database maintenance job failed: %s", e)


limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    await api_startup()

    logger.info("Running startup tasks...")
    clear_temp_uploads()

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(run_database_maintenance, "interval", days=1)
    scheduler.start()
    logger.info("Scheduler started for daily database maintenance.")

    yield

    await api_shutdown()


app = FastAPI(
    title="Clinical Compliance Analyzer API",
    description="API for analyzing clinical documents for compliance.",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, http_exception_handler)

app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(users.router, tags=["Users"])
app.include_router(analysis.router, tags=["Analysis"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(compliance.router, tags=["Compliance"])


@app.get("/")
def read_root():
    """Root endpoint providing API welcome message."""
    return {"message": "Welcome to the Clinical Compliance Analyzer API"}
