#!/usr/bin/env python3
"""
Unified startup script for the Therapy Compliance Analyzer.
Launches the backend API and the frontend GUI.
"""

import sys
import subprocess
import atexit
import time
import os
import structlog

from src.logging_config import setup_logging

# --- Path Setup ---
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Hugging Face Cache Setup ---
# Set a local cache directory for Hugging Face models to improve deployment.
cache_dir = os.path.join(project_root, ".cache")
os.environ["HF_HUB_CACHE"] = cache_dir
os.makedirs(cache_dir, exist_ok=True)

# --- Logging ---
# Configure structured logging for the application
setup_logging()
logger = structlog.get_logger(__name__)

# Global variable to hold the API process
api_process = None


def start_api_server():
    """Launches the Uvicorn API server as a background process."""
    global api_process
    try:
        logger.info("Starting backend API server...")
        # Use sys.executable to ensure we're using the same Python interpreter
        command = [
            sys.executable,
            "-m",
            "uvicorn",
            "src.api.main:app",
            "--port",
            "8000",
        ]

        # Open log files for stdout and stderr
        api_log_out = open("api_server.log", "a")
        api_log_err = open("api_server.err.log", "a")

        api_process = subprocess.Popen(
            command,
            stdout=api_log_out,
            stderr=api_log_err,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        logger.info(f"API server started with PID: {api_process.pid}")
        # Register the cleanup function to be called on exit
        atexit.register(cleanup_api_server)
        return True
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        return False


def cleanup_api_server():
    """Ensures the API server process is terminated."""
    global api_process
    if api_process:
        logger.info(f"Shutting down API server (PID: {api_process.pid})...")
        api_process.terminate()
        try:
            # Wait for a few seconds for the process to terminate
            api_process.wait(timeout=5)
            logger.info("API server shut down successfully.")
        except subprocess.TimeoutExpired:
            logger.warning("API server did not terminate in time, killing it.")
            api_process.kill()
        api_process = None


def main():
    """Main application entry point."""
    # Remove Qt platform override to allow normal GUI
    # os.environ["QT_QPA_PLATFORM"] = "offscreen"

    # Start the Therapy Compliance Analyzer GUI (standalone mode)
    try:
        logger.info("Starting Therapy Compliance Analyzer GUI (Standalone Mode)...")
        from PyQt6.QtWidgets import QApplication
        from src.gui.therapy_compliance_window import TherapyComplianceWindow

        app = QApplication(sys.argv)
        app.setApplicationName("Therapy Compliance Analyzer - PT | OT | SLP")

        main_win = TherapyComplianceWindow()
        main_win.show()

        exit_code = app.exec()
        logger.info(f"Application exited with code {exit_code}.")
        return exit_code

    except Exception as e:
        logger.error(f"An unexpected error occurred in the GUI application: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
