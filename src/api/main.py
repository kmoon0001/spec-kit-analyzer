"""
Clinical Compliance Analyzer API

FastAPI backend for the Therapy Compliance Analyzer desktop application.
Provides endpoints for document analysis, user management, and compliance reporting.
"""
import os
import shutil
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from apscheduler.schedulers.background import BackgroundScheduler

from .dependencies import startup_event as api_startup, shutdown_event as api_shutdown
from .routers import auth, analysis, dashboard, admin, health, chat, compliance, users, synergy, review
from .error_handling import http_exception_handler
from ..core.database_maintenance_service import DatabaseMaintenanceService
from ..config import get_settings

settings = get_settings()

# --- Configuration ---
DATABASE_PURGE_RETENTION_DAYS = settings.maintenance.purge_retention_days
TEMP_UPLOAD_DIR = settings.temp_upload_dir

# --- Logging ---
logger = logging.getLogger(__name__)


# --- Helper Functions ---
def clear_temp_uploads():
    """Clears all files from the temporary upload directory."""
    if os.path.exists(TEMP_UPLOAD_DIR):
        for filename in os.listdir(TEMP_UPLOAD_DIR):
            file_path = os.path.join(TEMP_UPLOAD_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                logger.info("Successfully cleaned up temporary file: %s", file_path)
            except (OSError, PermissionError) as e:
                logger.error("Failed to delete %s. Reason: %s", file_path, e)


def run_database_maintenance():
    """Instantiates and runs the database maintenance service."""
    logger.info("Scheduler triggered: Starting database maintenance job.")
    maintenance_service = DatabaseMaintenanceService()
    maintenance_service.purge_old_reports(retention_days=DATABASE_PURGE_RETENTION_DAYS)