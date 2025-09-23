import sys
import os
from PySide6.QtWidgets import QApplication
from gui.main_window import MainApplicationWindow, initialize_database

if __name__ == '__main__':
    # Add the project root to the Python path to allow imports from 'src'
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    app = QApplication(sys.argv)

    # The database should likely be part of the backend now,
    # but for now, we'll keep the initialization here to
    # ensure the GUI can still run. We can refactor this later.
    initialize_database()

    main_win = MainApplicationWindow()
    main_win.show()

    sys.exit(app.exec())
