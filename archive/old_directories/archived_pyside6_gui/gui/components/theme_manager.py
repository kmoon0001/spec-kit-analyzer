"""Theme Manager - Centralized theme management
import numpy as np
Handles application-wide theme switching and styling.
"""

from enum import Enum

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication


class ThemeType(Enum):
    """Available theme types."""

    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class ThemeManager(QObject):
    """Centralized theme management for the application.

    Signals:
        theme_changed: Emitted when theme changes (theme_name: str)
    """

    theme_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.current_theme = ThemeType.LIGHT

    def set_theme(self, theme: ThemeType):
        """Set the application theme."""
        if theme != self.current_theme:
            self.current_theme = theme
            self.apply_theme()
            self.theme_changed.emit(theme.value)

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        if self.current_theme == ThemeType.LIGHT:
            self.set_theme(ThemeType.DARK)
        else:
            self.set_theme(ThemeType.LIGHT)

    def apply_theme(self):
        """Apply the current theme to the application."""
        app = QApplication.instance()
        if app:
            if self.current_theme == ThemeType.DARK:
                app.setStyleSheet(self.get_dark_theme_stylesheet())
            else:
                app.setStyleSheet(self.get_light_theme_stylesheet())

    def get_current_theme(self) -> ThemeType:
        """Get the current theme."""
        return self.current_theme

    def is_dark_theme(self) -> bool:
        """Check if current theme is dark."""
        return self.current_theme == ThemeType.DARK

    def get_light_theme_stylesheet(self) -> str:
        """Get the light theme stylesheet."""
        return """
        /* Light Theme Stylesheet */
        QMainWindow {
            background-color: #ffffff;
            color: #333333;
        }

        QWidget {
            background-color: #ffffff;
            color: #333333;
        }

        /* Group Boxes */
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
            background-color: #fafafa;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #333333;
        }

        /* Buttons */
        QPushButton {
            background: #4a90e2;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
            min-height: 20px;
        }

        QPushButton:hover {
            background: #357abd;
        }

        QPushButton:pressed {
            background: #2968a3;
        }

        QPushButton:disabled {
            background: #cccccc;
            color: #666666;
        }

        /* Tab Widget */
        QTabWidget::pane {
            border: 1px solid #cccccc;
            border-radius: 8px;
            background: white;
        }

        QTabBar::tab {
            background: #f0f0f0;
            color: #333333;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            min-width: 80px;
        }

        QTabBar::tab:selected {
            background: #4a90e2;
            color: white;
        }

        QTabBar::tab:hover:!selected {
            background: #e0e0e0;
        }

        /* Text Widgets */
        QTextBrowser, QTextEdit, QPlainTextEdit {
            border: 1px solid #cccccc;
            border-radius: 6px;
            padding: 8px;
            background: white;
            color: #333333;
        }

        /* Input Widgets */
        QLineEdit, QComboBox {
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 4px 8px;
            background: white;
            color: #333333;
            min-height: 20px;
        }

        QLineEdit:focus, QComboBox:focus {
            border-color: #4a90e2;
        }

        QComboBox::drop-down {
            border: none;
            width: 20px;
        }

        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #333333;
        }

        /* Progress Bar */
        QProgressBar {
            border: 1px solid #cccccc;
            border-radius: 4px;
            text-align: center;
            background: #f0f0f0;
            color: #333333;
        }

        QProgressBar::chunk {
            background: #4a90e2;
            border-radius: 3px;
        }

        /* Status Bar */
        QStatusBar {
            background: #f8f9fa;
            color: #333333;
            border-top: 1px solid #dee2e6;
        }

        /* Menu Bar */
        QMenuBar {
            background: #f8f9fa;
            color: #333333;
            border-bottom: 1px solid #dee2e6;
        }

        QMenuBar::item {
            background: transparent;
            padding: 4px 8px;
        }

        QMenuBar::item:selected {
            background: #4a90e2;
            color: white;
        }

        QMenu {
            background: white;
            color: #333333;
            border: 1px solid #cccccc;
        }

        QMenu::item:selected {
            background: #4a90e2;
            color: white;
        }

        /* Splitter */
        QSplitter::handle {
            background: #cccccc;
        }

        QSplitter::handle:horizontal {
            width: 2px;
        }

        QSplitter::handle:vertical {
            height: 2px;
        }
        """

    def get_dark_theme_stylesheet(self) -> str:
        """Get the dark theme stylesheet."""
        return """
        /* Dark Theme Stylesheet */
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }

        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }

        /* Group Boxes */
        QGroupBox {
            font-weight: bold;
            border: 2px solid #555555;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
            background-color: #3a3a3a;
            color: #ffffff;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #ffffff;
        }

        /* Buttons */
        QPushButton {
            background: #0078d4;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
            min-height: 20px;
        }

        QPushButton:hover {
            background: #106ebe;
        }

        QPushButton:pressed {
            background: #005a9e;
        }

        QPushButton:disabled {
            background: #555555;
            color: #888888;
        }

        /* Tab Widget */
        QTabWidget::pane {
            border: 1px solid #555555;
            border-radius: 8px;
            background: #3a3a3a;
        }

        QTabBar::tab {
            background: #4a4a4a;
            color: #ffffff;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            min-width: 80px;
        }

        QTabBar::tab:selected {
            background: #0078d4;
            color: white;
        }

        QTabBar::tab:hover:!selected {
            background: #5a5a5a;
        }

        /* Text Widgets */
        QTextBrowser, QTextEdit, QPlainTextEdit {
            border: 1px solid #555555;
            border-radius: 6px;
            padding: 8px;
            background: #3a3a3a;
            color: #ffffff;
        }

        /* Input Widgets */
        QLineEdit, QComboBox {
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 4px 8px;
            background: #3a3a3a;
            color: #ffffff;
            min-height: 20px;
        }

        QLineEdit:focus, QComboBox:focus {
            border-color: #0078d4;
        }

        QComboBox::drop-down {
            border: none;
            width: 20px;
        }

        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #ffffff;
        }

        /* Progress Bar */
        QProgressBar {
            border: 1px solid #555555;
            border-radius: 4px;
            text-align: center;
            background: #3a3a3a;
            color: #ffffff;
        }

        QProgressBar::chunk {
            background: #0078d4;
            border-radius: 3px;
        }

        /* Status Bar */
        QStatusBar {
            background: #3a3a3a;
            color: #ffffff;
            border-top: 1px solid #555555;
        }

        /* Menu Bar */
        QMenuBar {
            background: #3a3a3a;
            color: #ffffff;
            border-bottom: 1px solid #555555;
        }

        QMenuBar::item {
            background: transparent;
            padding: 4px 8px;
        }

        QMenuBar::item:selected {
            background: #0078d4;
            color: white;
        }

        QMenu {
            background: #3a3a3a;
            color: #ffffff;
            border: 1px solid #555555;
        }

        QMenu::item:selected {
            background: #0078d4;
            color: white;
        }

        /* Splitter */
        QSplitter::handle {
            background: #555555;
        }

        QSplitter::handle:horizontal {
            width: 2px;
        }

        QSplitter::handle:vertical {
            height: 2px;
        }
        """
