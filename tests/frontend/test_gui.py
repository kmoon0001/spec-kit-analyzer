import sys
from PySide6.QtWidgets import QApplication
from frontend.gui.main_window import MainApplicationWindow

def test_main_window_title(qtbot):
    """Test if the main window has the correct title."""
    # QApplication instance is managed by pytest-qt
    window = MainApplicationWindow()
    qtbot.addWidget(window)
    assert window.windowTitle() == 'Therapy Compliance Analyzer'
