import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainApplicationWindow
from src.core.database import initialize_database

if __name__ == '__main__':
    app = QApplication(sys.argv)
    initialize_database()
    main_win = MainApplicationWindow()
    main_win.show()
    sys.exit(app.exec())
