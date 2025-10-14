"""
GUI entry point script.

This script launches the PySide6 GUI application with proper authentication.
"""

import sys
import time
from pathlib import Path

import requests

# Add project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Set matplotlib backend before importing any GUI components
import os

try:
    import matplotlib  # type: ignore[import-not-found]
except Exception:
    matplotlib = None  # type: ignore[assignment]

# Prefer PySide6; avoid hard failure if matplotlib is absent
os.environ["QT_API"] = "pyside6"
if matplotlib is not None:
    try:
        matplotlib.use("Qt5Agg")
    except Exception:
        pass

from PySide6.QtWidgets import QApplication, QMessageBox


def check_api_connection(max_attempts=5, delay=2):
    """Check if the API server is running and accessible."""
    print("Checking API server connection...")

    for attempt in range(max_attempts):
        try:
            response = requests.get("http://127.0.0.1:8001/health", timeout=5)
            if response.status_code == 200:
                print("SUCCESS: API server is running and accessible!")
                return True
        except requests.exceptions.RequestException as e:
            print(f"   Attempt {attempt + 1}/{max_attempts}: API not ready ({e})")

        if attempt < max_attempts - 1:
            time.sleep(delay)

    print("ERROR: API server is not accessible")
    return False


if __name__ == "__main__":
    try:
        print("Starting Therapy Compliance Analyzer GUI...")

        # Check if API is running
        if not check_api_connection():
            print("WARNING: API server not detected. Please start the API server first:")
            print("   python scripts/run_api.py")
            print("\nOr use the combined startup script:")
            print("   python scripts/start_application.py")

            # Show a dialog to the user
            app = QApplication(sys.argv)
    # Apply PyCharm dark theme
    app.setStyleSheet(pycharm_theme.get_application_stylesheet())
    logger.info("Applied PyCharm dark theme")

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("API Server Required")
            msg.setText("The API server is not running.")
            msg.setInformativeText(
                "Please start the API server first:\n\npython scripts/run_api.py\n\nOr use: python scripts/start_application.py"
            )
            msg.exec()
            sys.exit(1)

        # Use the proper authentication flow from src.gui.main
        from src.gui.main import main as gui_main
from src.gui.widgets.pycharm_dark_theme import pycharm_theme

        gui_main()

    except Exception as e:
        print(f"ERROR: Error starting application: {e}")
        import traceback

        traceback.print_exc()
        print("\nPlease ensure PySide6 is installed: pip install PySide6")
        sys.exit(1)
