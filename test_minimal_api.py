#!/usr/bin/env python3
"""
Minimal API test to debug startup issues.
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

def test_minimal_app():
    """Test creating a minimal FastAPI app."""
    try:
        from fastapi import FastAPI
        print("✓ FastAPI imported successfully")
        
        app = FastAPI(title="Test API")
        print("✓ FastAPI app created successfully")
        
        @app.get("/health")
        async def health():
            return {"status": "ok"}
        
        print("✓ Health endpoint added")
        
        import uvicorn
        print("✓ Uvicorn imported successfully")
        
        print("Starting server...")
        uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_minimal_app()
