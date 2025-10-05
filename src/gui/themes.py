"""
Theme definitions for the application GUI.

This module centralizes the color palettes for different UI themes,
making it easy to add, remove, or modify themes without changing the
main application logic.
"""
from __future__ import annotations

from typing import Dict

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

ThemeColors = Dict[QPalette.ColorRole, QColor]

THEMES: Dict[str, ThemeColors] = {
    "dark": {
        QPalette.Window: QColor(30, 34, 43),
        QPalette.WindowText: QColor(255, 255, 255),
        QPalette.Base: QColor(24, 26, 32),
        QPalette.AlternateBase: QColor(30, 34, 43),
        QPalette.ToolTipBase: QColor(255, 255, 255),
        QPalette.ToolTipText: QColor(255, 255, 255),
        QPalette.Text: QColor(255, 255, 255),
        QPalette.Button: QColor(45, 49, 60),
        QPalette.ButtonText: QColor(255, 255, 255),
        QPalette.Highlight: QColor(14, 165, 233),
        QPalette.HighlightedText: QColor(255, 255, 255),
    }
}

def get_theme_palette(theme_name: str) -> QPalette:
    """Returns a QPalette for the given theme name."""
    if theme_name in THEMES:
        palette = QPalette()
        for role, color in THEMES[theme_name].items():
            palette.setColor(role, color)
        return palette
    # Fallback for 'light' or unknown themes
    return QApplication.style().standardPalette()