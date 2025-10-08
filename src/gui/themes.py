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

ColorRole = QPalette.ColorRole
ThemeColors = Dict[ColorRole, QColor]

THEMES: Dict[str, ThemeColors] = {
    "dark": {
        # True dark theme - no light colors
        ColorRole.Window: QColor(30, 30, 30),          # Dark background
        ColorRole.WindowText: QColor(220, 220, 220),   # Light text on dark
        ColorRole.Base: QColor(25, 25, 25),            # Darker for input fields
        ColorRole.AlternateBase: QColor(45, 45, 45),   # Slightly lighter for alternating rows
        ColorRole.ToolTipBase: QColor(50, 50, 50),     # Dark tooltips
        ColorRole.ToolTipText: QColor(220, 220, 220),  # Light tooltip text
        ColorRole.Text: QColor(220, 220, 220),         # Light text
        ColorRole.Button: QColor(45, 45, 45),          # Dark buttons
        ColorRole.ButtonText: QColor(220, 220, 220),   # Light button text
        ColorRole.Highlight: QColor(0, 120, 215),      # Blue highlight
        ColorRole.HighlightedText: QColor(255, 255, 255), # White text on highlight
        ColorRole.Link: QColor(100, 150, 255),         # Light blue links
        ColorRole.LinkVisited: QColor(150, 100, 255),  # Purple visited links
    },
    "light": {
        # Clean light theme
        ColorRole.Window: QColor(248, 249, 250),       # Very light gray background
        ColorRole.WindowText: QColor(33, 37, 41),      # Dark text
        ColorRole.Base: QColor(255, 255, 255),         # White input fields
        ColorRole.AlternateBase: QColor(245, 245, 245), # Light gray alternating
        ColorRole.ToolTipBase: QColor(255, 255, 220),  # Light yellow tooltips
        ColorRole.ToolTipText: QColor(0, 0, 0),        # Black tooltip text
        ColorRole.Text: QColor(33, 37, 41),            # Dark text
        ColorRole.Button: QColor(240, 240, 240),       # Light gray buttons
        ColorRole.ButtonText: QColor(33, 37, 41),      # Dark button text
        ColorRole.Highlight: QColor(0, 120, 215),      # Blue highlight
        ColorRole.HighlightedText: QColor(255, 255, 255), # White text on highlight
        ColorRole.Link: QColor(0, 100, 200),           # Blue links
        ColorRole.LinkVisited: QColor(100, 0, 200),    # Purple visited links
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
