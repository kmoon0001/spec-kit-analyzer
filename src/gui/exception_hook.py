import sys
import traceback
from PyQt6.QtWidgets import QMessageBox
from src.utils.logger import get_logger

logger = get_logger(__name__)

def global_exception_hook(exctype, value, tb):
    """
    A global exception hook to catch unhandled exceptions in the PyQt5 application.
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
    error_box.exec_()

    # It's generally a good idea to exit the application after an unhandled exception
    sys.exit(1)

def install_exception_hook():
    """
    Installs the global exception hook.
    """
    sys.excepthook = global_exception_hook
