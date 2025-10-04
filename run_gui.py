"""
GUI entry point script.

This script launches the PyQt6 GUI application.
"""
import sys
from pathlib import Path
import asyncio
from PySide6.QtWidgets import QApplication

# Add project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.gui.main_window_ultimate import UltimateMainWindow as MainApplicationWindow
from src.database import init_db

if __name__ == "__main__":
    # Initialize the database first to ensure tables are created
    asyncio.run(init_db())

    # Create and run the application
    app = QApplication(sys.argv)
    main_win = MainApplicationWindow()
    main_win.start()  # This shows the window and loads the UI
    sys.exit(app.exec())