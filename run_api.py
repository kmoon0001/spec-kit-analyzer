"""
API entry point script.

This script launches the FastAPI application using a Uvicorn server.
"""
import sys
import signal
import os
import time
from pathlib import Path
import uvicorn

# Add project root to the Python path to allow for `src` imports
# This is necessary because the script is in the root directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Global flag to control server shutdown
server_running = True

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global server_running
    print(f"\n🛑 Received signal {signum}. Shutting down API server...")
    server_running = False
    sys.exit(0)

def check_dependencies():
    """Check if all required dependencies are available."""
    try:
        # Test critical imports
        from src.api.main import app
        from src.config import get_settings
        print("✅ All dependencies loaded successfully")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

if __name__ == "__main__":
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Starting Therapy Compliance Analyzer API Server...")
    print("   Host: 127.0.0.1")
    print("   Port: 8001")
    print("   Press Ctrl+C to stop")
    print("-" * 50)
    
    # Check dependencies first
    if not check_dependencies():
        print("❌ Dependency check failed. Please install requirements.")
        sys.exit(1)
    
    try:
        # Import the app instance here to ensure the path is set up correctly
        from src.api.main import app
        
        # Run the server directly with uvicorn
        print("🔄 Starting server...")
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8001,
            log_level="info",
            reload=False,  # Disable reload for stability
            access_log=True,
            timeout_keep_alive=30,
        )
        
    except KeyboardInterrupt:
        print("\n✅ API server stopped by user")
    except Exception as e:
        print(f"\n❌ API server error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("🧹 API server cleanup complete")