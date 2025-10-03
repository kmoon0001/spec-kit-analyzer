"""
API entry point script.

This script launches the FastAPI application using a Uvicorn server.
"""
import sys
from pathlib import Path
import uvicorn

# Add project root to the Python path to allow for `src` imports
# This is necessary because the script is in the root directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    # We import the app instance here to ensure the path is set up correctly
    from src.api.main import app

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=9000,
        log_level="info",
    )
