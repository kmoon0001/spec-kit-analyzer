import sys
import os
from unittest.mock import patch

# Add the src directory to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainApplicationWindow as MainWindow

if __name__ == '__main__':
    app = QApplication.instance()
    if app is None:
        print("Creating QApplication...")
        app = QApplication(sys.argv)

    print("Patching MainWindow._init_llm_thread...")
    with patch.object(MainWindow, '_init_llm_thread', return_value=None):
        print("Creating MainWindow instance...")
        window = MainWindow()
        print("MainWindow instance created.")
        # We don't call window.show() or app.exec() because we just want to see if instantiation crashes.

    print("Success: MainWindow was instantiated without crashing.")
