"""
Clinical Compliance Analyzer API

FastAPI backend for the Therapy Compliance Analyzer desktop application.
Provides endpoints for document analysis, user management, and compliance reporting.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from apscheduler.schedulers.background import BackgroundScheduler

from ..config import get_settings
from ..core.database_maintenance_service import run_database_maintenance
from ..utils.file_utils import clear_temp_uploads
from .dependencies import startup_event as api_startup, shutdown_event as api_shutdown
from .routers import auth, analysis, dashboard, admin, health, chat, compliance

# --- Logging ---
logger = logging.getLogger(__name__)

# --- FastAPI App Setup ---
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])
scheduler = BackgroundScheduler(daemon=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application's lifespan, handling startup and shutdown events.

    - Initializes AI models and other services on startup.
    - Clears temporary files from previous runs.
    - Starts and gracefully shuts down a background scheduler for maintenance tasks.
    """
    # --- Startup ---
    settings = get_settings()
    logger.info("Application startup sequence initiated.")

    # 1. Run API-level startup logic (e.g., loading AI models).
    await api_startup()

    # 2. Clean up any orphaned temporary files from previous runs.
    logger.info("Clearing temporary upload directory...")
    clear_temp_uploads(str(settings.paths.temp_upload_dir))

    # 3. Initialize and start the background scheduler for database maintenance.
    try:
        scheduler.add_job(
            run_database_maintenance,
            "interval",
            days=settings.maintenance.purge_interval_days,
            id="database_maintenance_job",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Background scheduler started for daily database maintenance.")
    except Exception as e:
        logger.critical("Failed to start background scheduler: %s", e, exc_info=True)

    yield

    # --- Shutdown ---
    logger.info("Application shutdown sequence initiated.")

    # 1. Gracefully shut down the background scheduler.
    if scheduler.running:
        logger.info("Shutting down background scheduler...")
        try:
            scheduler.shutdown()
            logger.info("Background scheduler shut down successfully.")
        except Exception as e:
            logger.error("Error during scheduler shutdown: %s", e, exc_info=True)

    # 2. Run API-level shutdown logic (if any).
    await api_shutdown()
    logger.info("Application shutdown complete.")


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
app.include_router(analysis.router, tags=["Analysis"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(compliance.router, tags=["Compliance"])


@app.get("/")
def read_root():
    """Root endpoint providing API welcome message."""
    return {"message": "Welcome to the Clinical Compliance Analyzer API"}
