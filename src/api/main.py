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
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from apscheduler.schedulers.background import BackgroundScheduler
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.dependencies import startup_event as api_startup, shutdown_event as api_shutdown
from src.api.routers import auth, analysis, dashboard, admin, health, chat, compliance
from src.api.error_handling import http_exception_handler
from src.config import get_settings
from src.utils.file_utils import clear_temp_uploads # Added import
from src.core.database_maintenance_service import run_database_maintenance # Added import
from src.api.rate_limiter import limiter # Added import

settings = get_settings()

# --- Logging ---
logger = logging.getLogger(__name__)


# --- Helper Functions ---






# --- FastAPI App Setup ---
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])
scheduler = BackgroundScheduler(daemon=True)


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
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

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
