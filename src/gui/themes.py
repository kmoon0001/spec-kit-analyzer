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
        # True dark theme - no light colors
        QPalette.Window: QColor(30, 30, 30),          # Dark background
        QPalette.WindowText: QColor(220, 220, 220),   # Light text on dark
        QPalette.Base: QColor(25, 25, 25),            # Darker for input fields
        QPalette.AlternateBase: QColor(45, 45, 45),   # Slightly lighter for alternating rows
        QPalette.ToolTipBase: QColor(50, 50, 50),     # Dark tooltips
        QPalette.ToolTipText: QColor(220, 220, 220),  # Light tooltip text
        QPalette.Text: QColor(220, 220, 220),         # Light text
        QPalette.Button: QColor(45, 45, 45),          # Dark buttons
        QPalette.ButtonText: QColor(220, 220, 220),   # Light button text
        QPalette.Highlight: QColor(0, 120, 215),      # Blue highlight
        QPalette.HighlightedText: QColor(255, 255, 255), # White text on highlight
        QPalette.Link: QColor(100, 150, 255),         # Light blue links
        QPalette.LinkVisited: QColor(150, 100, 255),  # Purple visited links
        QPalette.Disabled: QColor(100, 100, 100),     # Disabled elements
    },
    "light": {
        # Clean light theme
        QPalette.Window: QColor(248, 249, 250),       # Very light gray background
        QPalette.WindowText: QColor(33, 37, 41),      # Dark text
        QPalette.Base: QColor(255, 255, 255),         # White input fields
        QPalette.AlternateBase: QColor(245, 245, 245), # Light gray alternating
        QPalette.ToolTipBase: QColor(255, 255, 220),  # Light yellow tooltips
        QPalette.ToolTipText: QColor(0, 0, 0),        # Black tooltip text
        QPalette.Text: QColor(33, 37, 41),            # Dark text
        QPalette.Button: QColor(240, 240, 240),       # Light gray buttons
        QPalette.ButtonText: QColor(33, 37, 41),      # Dark button text
        QPalette.Highlight: QColor(0, 120, 215),      # Blue highlight
        QPalette.HighlightedText: QColor(255, 255, 255), # White text on highlight
        QPalette.Link: QColor(0, 100, 200),           # Blue links
        QPalette.LinkVisited: QColor(100, 0, 200),    # Purple visited links
        QPalette.Disabled: QColor(150, 150, 150),     # Disabled elements
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