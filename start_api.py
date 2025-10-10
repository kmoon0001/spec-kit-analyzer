#!/usr/bin/env python3
"""
Start the FastAPI backend server.
"""

import uvicorn
from src.api.main import app

def main():
    """Start the API server."""
    print("🚀 Starting Therapy Compliance Analyzer API...")
    
    # Start the server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=False  # Disable reload for stability
    )

if __name__ == "__main__":
    main()