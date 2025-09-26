import os
import shutil
import logging
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from apscheduler.schedulers.background import BackgroundScheduler

# Import all the modular routers
from .routers import auth, analysis, dashboard, admin, health, chat
from ..core.database_maintenance_service import DatabaseMaintenanceService
from .dependencies import startup_event as api_startup, shutdown_event as api_shutdown

# --- Configuration ---
DATABASE_PURGE_RETENTION_DAYS = 7  # Days to keep old reports
TEMP_UPLOAD_DIR = "tmp/uploads"

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
                logger.info(f"Successfully cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete {file_path}. Reason: {e}")

def run_database_maintenance():
    """Instantiates and runs the database maintenance service."""
    logger.info("Scheduler triggered: Starting database maintenance job.")
    maintenance_service = DatabaseMaintenanceService()
    maintenance_service.purge_old_reports(retention_days=DATABASE_PURGE_RETENTION_DAYS)
    logger.info("Scheduler job: Database maintenance finished.")

# --- FastAPI App Setup ---
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])
app = FastAPI(
    title="Clinical Compliance Analyzer API",
    description="API for analyzing clinical documents for compliance.",
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    """
    Actions to perform on application startup.
    - Clears the temporary upload directory.
    - Schedules the database maintenance job.
    - Initializes API services like the retriever.
    """
    # 1. Run API-level startup logic (e.g., model loading)
    await api_startup()

    # 2. Clean up any orphaned temporary files from previous runs
    logger.info("Running startup tasks...")
    clear_temp_uploads()

    # 3. Initialize and start the background scheduler
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(run_database_maintenance, 'interval', days=1)
    scheduler.start()
    logger.info("Scheduler started. Database maintenance job is scheduled to run daily.")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Actions to perform on application shutdown.
    """
    await api_shutdown()

# Add middleware and exception handlers
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include all the routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Clinical Compliance Analyzer API"}
