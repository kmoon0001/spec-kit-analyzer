"""
API entry point script.

This script launches the FastAPI application using a Uvicorn server.
"""
import sys
import signal
from pathlib import Path
import uvicorn

# Add project root to the Python path to allow for `src` imports
# This is necessary because the script is in the root directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\n🛑 Received signal {signum}. Shutting down API server...")
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Starting Therapy Compliance Analyzer API Server...")
    print("   Host: 127.0.0.1")
    print("   Port: 8001")
    print("   Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        # We import the app instance here to ensure the path is set up correctly
        from src.api.main import app

        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8001,
            log_level="info",
            reload=False,  # Disable reload for stability
            access_log=True,
        )
    except KeyboardInterrupt:
        print("\n✅ API server stopped by user")
    except Exception as e:
        print(f"\n❌ API server error: {e}")
        sys.exit(1)