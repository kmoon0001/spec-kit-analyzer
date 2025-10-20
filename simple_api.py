#!/usr/bin/env python3
"""
Simplified API server that bypasses problematic startup components
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Therapy Compliance Analyzer API",
    description="AI-powered clinical documentation compliance analysis",
    version="1.0.0",
)

# CORS configuration
ALLOWED_CORS_ORIGINS = [
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "https://127.0.0.1",
    "https://127.0.0.1:3000",
    "https://127.0.0.1:3001",
    "https://localhost",
    "https://localhost:3000",
    "https://localhost:3001",
    "app://.",
    "file://",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
)

@app.get("/")
def read_root():
    """Root endpoint providing API welcome message."""
    return {"message": "Welcome to the Clinical Compliance Analyzer API"}

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/api/health")
def api_health():
    """API health check endpoint."""
    return {"status": "healthy", "api": "running"}

# Add a simple analysis endpoint for testing
@app.post("/api/analysis/test")
def test_analysis():
    """Test analysis endpoint."""
    return {
        "status": "success",
        "message": "Analysis endpoint is working",
        "progress": 100
    }

# Add a simple upload endpoint for testing
@app.post("/api/upload/test")
def test_upload():
    """Test upload endpoint."""
    return {
        "status": "success",
        "message": "Upload endpoint is working",
        "file_id": "test-123"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting simplified API server...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
