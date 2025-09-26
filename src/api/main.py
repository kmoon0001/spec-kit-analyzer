from fastapi import FastAPI, Depends
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .dependencies import app_state, get_analysis_service
from ..core.analysis_service import AnalysisService
from .routers import auth, analysis, dashboard, admin, health, chat

# --- App and Middleware Setup ---

limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])

app = FastAPI(
    title="Clinical Compliance Analyzer API",
    description="API for analyzing clinical documents for compliance.",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# --- Singleton Service Management ---

@app.on_event("startup")
def startup_event():
    """Load the heavy AI model on startup and store it in the app_state."""
    app_state['analysis_service'] = AnalysisService()

# --- Routers ---

app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(
    analysis.router,
    prefix="/analysis",
    tags=["Analysis"],
    dependencies=[Depends(get_analysis_service)]
)
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])

# --- Root Endpoint ---

@app.get("/")
def read_root():
    return {"message": "Welcome to the Clinical Compliance Analyzer API"}
