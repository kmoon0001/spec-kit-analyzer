#!/usr/bin/env python3
"""
Simple API starter for debugging
"""

import os
import sys

# Set environment variables for faster startup
os.environ["USE_AI_MOCKS"] = "true"
os.environ["API_PORT"] = "8100"

# Start the API directly
if __name__ == "__main__":
    import uvicorn
    from src.api.main import app
    
    print("Starting API server with mocks enabled...")
    print("API will be available at: http://127.0.0.1:8100")
    print("Health check: http://127.0.0.1:8100/health")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8100,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\nAPI server stopped by user")
    except Exception as e:
        print(f"Error starting API server: {e}")
        sys.exit(1)