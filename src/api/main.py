from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import all the modular routers
from .routers import (
    auth,
    analysis,
    dashboard,
    admin,
    health,
    chat,
)  # Import the new router

# 1. Create a rate limiter instance
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])

# 2. Create the FastAPI app
app = FastAPI(
    title="Clinical Compliance Analyzer API",
    description="API for analyzing clinical documents for compliance.",
    version="1.0.0",
)

# 3. Add the rate-limiting middleware and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 4. Include all the routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])  # Add the new router


@app.get("/")
def read_root():
    return {"message": "Welcome to the Clinical Compliance Analyzer API"}
