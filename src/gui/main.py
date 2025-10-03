import sys
import asyncio
from PySide6.QtWidgets import QApplication

# Import the main window and the database initializer
from src.gui.main_window import MainApplicationWindow
from src.database import init_db

if __name__ == "__main__":
    # Initialize the database first to ensure tables are created
    asyncio.run(init_db())

    # Create and run the application
    app = QApplication(sys.argv)
    main_win = MainApplicationWindow()
    # The main window will be shown after a successful login
    sys.exit(app.exec())
