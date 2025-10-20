#!/usr/bin/env python3
"""
Minimal API server to test basic functionality
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
    title="Therapy Compliance Analyzer API - Minimal",
    description="Minimal version for testing",
    version="1.0.0",
)

# Basic CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Welcome to the Clinical Compliance Analyzer API - Minimal Version"}

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "minimal"}

@app.get("/test")
def test_endpoint():
    """Test endpoint."""
    return {"message": "Test endpoint working"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting minimal API server...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
