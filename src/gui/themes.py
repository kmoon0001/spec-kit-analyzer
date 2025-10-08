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
        # PyCharm Dracula-inspired colors with teal and purple accents
        QPalette.Window: QColor(40, 42, 54),          # Dracula background
        QPalette.WindowText: QColor(248, 248, 242),   # Dracula foreground
        QPalette.Base: QColor(33, 34, 44),            # Darker dracula for input fields
        QPalette.AlternateBase: QColor(68, 71, 90),   # Dracula selection
        QPalette.ToolTipBase: QColor(68, 71, 90),     # Dracula selection for tooltips
        QPalette.ToolTipText: QColor(248, 248, 242),  # Dracula foreground for tooltips
        QPalette.Text: QColor(248, 248, 242),         # Dracula foreground
        QPalette.Button: QColor(68, 71, 90),          # Dracula selection for buttons
        QPalette.ButtonText: QColor(248, 248, 242),   # Dracula foreground for buttons
        QPalette.Highlight: QColor(139, 233, 253),    # Kiro teal for highlights
        QPalette.HighlightedText: QColor(40, 42, 54), # Dark text on teal highlight
    },
    "light": {
        # Keep the original light theme
        QPalette.Window: QColor(255, 255, 255),
        QPalette.WindowText: QColor(0, 0, 0),
        QPalette.Base: QColor(255, 255, 255),
        QPalette.AlternateBase: QColor(245, 245, 245),
        QPalette.ToolTipBase: QColor(255, 255, 220),
        QPalette.ToolTipText: QColor(0, 0, 0),
        QPalette.Text: QColor(0, 0, 0),
        QPalette.Button: QColor(240, 240, 240),
        QPalette.ButtonText: QColor(0, 0, 0),
        QPalette.Highlight: QColor(0, 120, 215),
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