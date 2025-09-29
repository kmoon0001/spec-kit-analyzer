"""
Clinical Compliance Analyzer API

FastAPI backend for the Therapy Compliance Analyzer desktop application.
Provides endpoints for document analysis, user management, and compliance reporting.
"""
import os
import shutil
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from apscheduler.schedulers.background import BackgroundScheduler

from .dependencies import startup_event as api_startup, shutdown_event as api_shutdown
from .routers import auth, analysis, dashboard, admin, health, chat, compliance, users, synergy, review
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
    logger.info("Scheduler job: Database maintenance finished.")


# --- FastAPI App Setup ---
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    # 1. Run API-level startup logic (e.g., model loading)
    await api_startup()

    # 2. Clean up any orphaned temporary files from previous runs
    logger.info("Running startup tasks...")
    clear_temp_uploads()

    # 3. Initialize and start the background scheduler
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(run_database_maintenance, "interval", days=1)
    scheduler.start()
    logger.info("Scheduler started for daily database maintenance.")

    yield

    # Shutdown
    await api_shutdown()

app = FastAPI(
    title="Clinical Compliance Analyzer API",
    description="API for analyzing clinical documents for compliance.",
    version="1.0.0",
    lifespan=lifespan,
)


# --- Middleware and Exception Handlers ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Routers ---
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(users.router, tags=["Users"])
app.include_router(analysis.router, tags=["Analysis"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(compliance.router, tags=["Compliance"])
app.include_router(synergy.router, prefix="/synergy", tags=["Synergy"])
app.include_router(review.router, prefix="/reviews", tags=["Reviews"])


@app.get("/")
def read_root():
    """Root endpoint providing API welcome message."""
    return {"message": "Welcome to the Clinical Compliance Analyzer API"}
