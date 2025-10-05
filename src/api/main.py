"""
Clinical Compliance Analyzer API

FastAPI backend for the Therapy Compliance Analyzer desktop application.
Provides endpoints for document analysis, user management, and compliance reporting.
"""

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
from src.api.routers import (
    admin,
    analysis,
    auth,
    chat,
    compliance,
    dashboard,
    health,
    habits,
    meta_analytics,
)
from src.api.global_exception_handler import (
    global_exception_handler,
    http_exception_handler,
)
from src.core.database_maintenance_service import DatabaseMaintenanceService
from src.core.data_purging_service import DataPurgingService
from src.config import get_settings
from src.logging_config import CorrelationIdMiddleware

settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])

logger = structlog.get_logger(__name__)

def run_maintenance_jobs():
    """Instantiates and runs all scheduled maintenance services."""
    logger.info("Scheduler triggered: Starting all maintenance jobs.")
    try:
        db_maintenance = DatabaseMaintenanceService()
        db_maintenance.purge_old_reports(settings.maintenance.purge_retention_days)
        
        data_purging = DataPurgingService()
        data_purging.purge_all()
        
        logger.info("Scheduler jobs completed successfully.")
    except Exception as e:
        logger.exception("A maintenance job failed", error=str(e))

scheduler = BackgroundScheduler(daemon=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    await api_startup()
    
    # Run an initial purge on startup to clear out any old data
    run_maintenance_jobs()

    # Schedule recurring maintenance
    scheduler.add_job(run_maintenance_jobs, "interval", days=1)
    scheduler.start()
    logger.info("Scheduler started for daily maintenance tasks.")

    yield

    await api_shutdown()
    scheduler.shutdown()

app = FastAPI(
    title="Therapy Compliance Analyzer API",
    description="""
## Overview

The Therapy Compliance Analyzer API provides comprehensive endpoints for analyzing clinical 
therapy documentation for compliance with Medicare and regulatory guidelines.

### Key Features

* **🔒 Secure Authentication**: JWT-based authentication with role-based access control
* **📄 Document Analysis**: Multi-format support (PDF, DOCX, TXT) with OCR capabilities
* **🤖 AI-Powered Analysis**: Local LLM processing for compliance checking
* **📊 Dashboard Analytics**: Historical compliance trends and performance metrics
* **💬 AI Chat Assistant**: Contextual compliance guidance and clarification
* **📋 Rubric Management**: Custom compliance rule creation and management
* **🔐 HIPAA Compliant**: All processing occurs locally, no external data transmission

### Security

All endpoints require authentication via JWT Bearer token except for:
- `/` (root)
- `/health` (health check)
- `/auth/token` (login)
- `/docs` and `/redoc` (API documentation)

### Data Privacy

- All AI/ML processing occurs locally
- No patient data is transmitted to external services
- Automatic PHI scrubbing and redaction
- Configurable data retention and auto-purge

### Support

For technical support or questions, please refer to the project documentation or contact 
the development team.
    """,
    version="1.0.0",
    lifespan=lifespan,
    contact={
        "name": "Therapy Compliance Analyzer Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://example.com/license",
    },
    terms_of_service="https://example.com/terms",
    openapi_tags=[
        {"name": "Health", "description": "System health and status monitoring endpoints"},
        {"name": "Authentication", "description": "User authentication and session management"},
        {"name": "Analysis", "description": "Document upload and compliance analysis operations"},
        {"name": "Dashboard", "description": "Analytics and historical compliance data"},
        {"name": "Chat", "description": "AI-powered compliance assistance and guidance"},
        {"name": "Compliance", "description": "Rubric management and compliance rule operations"},
        {"name": "Admin", "description": "Administrative operations (admin users only)"},
    ],
)

app.add_middleware(CorrelationIdMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(analysis.router, tags=["Analysis"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(compliance.router, tags=["Compliance"])
app.include_router(habits.router, tags=["Habits"])
app.include_router(meta_analytics.router, tags=["Meta Analytics"])

@app.get("/")
def read_root():
    """Root endpoint providing API welcome message."""
    return {"message": "Welcome to the Clinical Compliance Analyzer API"}
