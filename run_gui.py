"""
GUI entry point script.

This script launches the PySide6 GUI application.
"""
import sys
from pathlib import Path
import asyncio

# Add project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Set matplotlib backend before importing any GUI components
import matplotlib
import os
# Force matplotlib to use the correct backend for PySide6
os.environ['QT_API'] = 'pyside6'
matplotlib.use('Qt5Agg')

from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainApplicationWindow
from src.database import init_db

if __name__ == "__main__":
    try:
        # Initialize the database first to ensure tables are created
        asyncio.run(init_db())

        # Create and run the application
        app = QApplication(sys.argv)
        main_win = MainApplicationWindow()
        main_win.start()  # This shows the window and loads the UI
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Error starting application: {e}")
        print("Please ensure PySide6 is installed: pip install PySide6")
        sys.exit(1)