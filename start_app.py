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
import logging

# --- Path Setup ---
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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
    # Set the Qt platform plugin for headless environments
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

    # 1. Initialize the database first
    logger.info("Initializing database schema...")
    try:
        subprocess.run([sys.executable, "initialize_db.py"], check=True)
        logger.info("Database initialized successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to initialize database: {e}")
        return 1

    # 2. Start the backend server
    if not start_api_server():
        logger.error(
            "Could not start the backend API. The application cannot continue."
        )
        return 1

    # 2. Give the server a moment to initialize
    logger.info("Waiting for API server to be ready...")
    time.sleep(5)  # Adjust as needed

    # 3. Start the GUI application
    try:
        logger.info("Starting GUI application...")
        from PyQt6.QtWidgets import QApplication
        from src.gui.main_window import MainApplicationWindow

        app = QApplication(sys.argv)
        app.setApplicationName("Therapy Compliance Analyzer")

        main_win = MainApplicationWindow()
        main_win.start()  # This should handle login and then show the window

        exit_code = app.exec()
        logger.info(f"GUI application exited with code {exit_code}.")
        return exit_code

    except Exception as e:
        logger.error(f"An unexpected error occurred in the GUI application: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        # Ensure cleanup is called, even if atexit fails
        cleanup_api_server()


if __name__ == "__main__":
    sys.exit(main())
