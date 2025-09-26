import sys
import os

# --- The Definitive Path Solution ---
# 1. Get the absolute path of the directory where this script is located.
# This will be the project's root directory.
project_root = os.path.dirname(os.path.abspath(__file__))

# 2. Add the project root to the Python path.
# This ensures that any `import src. ...` statements will work correctly.
sys.path.insert(0, project_root)

# 3. Now that the path is correct, we can import and run the application.
from PyQt6.QtWidgets import QApplication
from src.gui.main_window import MainApplicationWindow
from src.database import init_db

if __name__ == "__main__":
    print("Initializing database...")
    init_db()

    print("Starting GUI application...")
    app = QApplication(sys.argv)
    main_win = MainApplicationWindow()
    # Start the application logic (loading models, showing login) after the window is created.
    main_win.start()
    # The main window will be shown by the start() method after a successful login.
    sys.exit(app.exec())
