from fastapi import FastAPI

from .. import rubric_router
from .routers import auth, analysis, dashboard, users # Import the new users router

# Add metadata for the API
app = FastAPI(
    title="Clinical Compliance Analyzer API",
    description="API for analyzing clinical documents for compliance.",
    version="1.0.0",
)

# Include all the routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
app.include_router(rubric_router.router, prefix="/rubrics", tags=["rubrics"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(users.router, prefix="/api", tags=["users"]) # Add the new users router

@app.get("/")
def read_root():
    return {"message": "Welcome to the Clinical Compliance Analyzer API"}
