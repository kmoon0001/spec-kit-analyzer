import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import MainApplicationWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainApplicationWindow()
    main_win.show()
    sys.exit(app.exec())
