#!/usr/bin/env python3
"""
Simple API starter for debugging
"""

import os
import sys

# Set environment variables for full AI functionality
os.environ["USE_AI_MOCKS"] = "false"
os.environ["API_PORT"] = "8101"

# Start the API directly
if __name__ == "__main__":
    import uvicorn
    from src.api.main import app
    
    print("Starting API server with full AI models...")
    print("API will be available at: http://127.0.0.1:8101")
    print("Health check: http://127.0.0.1:8101/health")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8101,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\nAPI server stopped by user")
    except Exception as e:
        print(f"Error starting API server: {e}")
        sys.exit(1)