"""Kivy Theme System - Translated from the PySide6 medical_theme.py."""

from kivy.utils import get_color_from_hex

def get_theme_colors(theme='light'):
    colors = {
        "light": {
            "primary_blue": "#1d4ed8",
            "primary_green": "#047857",
            "kiro_black": "#0f172a",
            "medical_gray": "#475569",
            "bg_primary": "#f8fafc",
            "bg_secondary": "#e2e8f0",
            "bg_tertiary": "#cbd5e0",
            "bg_card": "#ffffff",
            "bg_hover": "#f1f5f9",
            "text_primary": "#0f172a",
            "text_secondary": "#334155",
            "text_muted": "#64748b",
            "text_inverse": "#ffffff",
            "border_light": "#cbd5e0",
            "border_medium": "#94a3b8",
            "border_dark": "#64748b",
            "border_focus": "#1d4ed8",
            "success": "#059669",
            "warning": "#d97706",
            "error": "#dc2626",
            "info": "#1d4ed8",
            "accent_1": "#7c3aed",
            "accent_2": "#0891b2",
        },
        "dark": {
            "primary_blue": "#8be9fd",
            "primary_green": "#50fa7b",
            "kiro_black": "#6272a4",
            "medical_gray": "#bd93f9",
            "bg_primary": "#1a1a1a",
            "bg_secondary": "#2d2d2d",
            "bg_tertiary": "#404040",
            "bg_card": "#2d2d2d",
            "bg_hover": "#404040",
            "text_primary": "#f8f8f2",
            "text_secondary": "#f8f8f2",
            "text_muted": "#6272a4",
            "text_inverse": "#282a36",
            "border_light": "#44475a",
            "border_medium": "#6272a4",
            "border_dark": "#bd93f9",
            "border_focus": "#8be9fd",
            "success": "#50fa7b",
            "warning": "#f1fa8c",
            "error": "#ff5555",
            "info": "#8be9fd",
            "accent_1": "#bd93f9",
            "accent_2": "#8be9fd",
        },
    }
    
    # Convert hex colors to Kivy's 0-1 RGBA format
    rgba_colors = {}
    for name, hex_code in colors[theme].items():
        rgba_colors[name] = get_color_from_hex(hex_code)
        
    return rgba_colors

# Provide a default theme for the kv file to use
colors = get_theme_colors('light')
