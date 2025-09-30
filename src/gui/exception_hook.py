import sys
import traceback
import logging
from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

def global_exception_hook(exctype, value, tb) -> None:
    """
    Global exception hook for unhandled exceptions in the PyQt6 application.
    Logs the error and shows a critical message box when possible.
    """
    traceback_details = "".join(traceback.format_exception(exctype, value, tb))
    error_message = (
        "An unexpected error occurred:\n\n"
        f"{value}\n\n"
        "Please check the logs for more details."
    )

    logger.error(f"Unhandled exception: {value}", exc_info=(exctype, value, tb))

    # Show a critical error message box to the user
    error_box = QMessageBox()
    error_box.setIcon(QMessageBox.Critical)
    error_box.setText(error_message)
    error_box.setWindowTitle("Unhandled Exception")
    error_box.setDetailedText(traceback_details)
    try:
        error_box.exec()
    except Exception:
        # In headless or abnormal states, exec() may fail; log and continue to exit
        logger.exception("Failed to display error dialog")

    # It's generally a good idea to exit the application after an unhandled exception
    sys.exit(1)

def install_exception_hook():
    """
    Installs the global exception hook.
    """
    sys.excepthook = global_exception_hook
