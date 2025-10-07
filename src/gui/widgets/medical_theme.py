"""
Medical Theme System - Professional medical UI styling with light/dark themes.
"""

from PySide6.QtCore import QObject, Signal


class MedicalTheme(QObject):
    """Medical theme manager with light/dark mode support."""

    theme_changed = Signal(str)  # Emits 'light' or 'dark'

    def __init__(self):
        super().__init__()
        self.current_theme = "light"

        # Medical color palette with improved contrast
        self.colors = {
            "light": {
                # Primary medical colors
                "primary_blue": "#1d4ed8",  # Darker medical blue for better contrast
                "primary_green": "#047857",  # Darker medical green
                "kiro_black": "#0f172a",  # Darker Kiro brand black
                "medical_gray": "#475569",  # Darker professional gray
                # Background colors
                "bg_primary": "#ffffff",  # Main background
                "bg_secondary": "#f8fafc",  # Secondary background
                "bg_tertiary": "#e2e8f0",  # More contrasted tertiary background
                "bg_card": "#ffffff",  # Card background
                "bg_hover": "#f1f5f9",  # Hover background
                # Text colors
                "text_primary": "#0f172a",  # Darker main text
                "text_secondary": "#334155",  # Darker secondary text
                "text_muted": "#64748b",  # Muted text
                "text_inverse": "#ffffff",  # White text for dark backgrounds
                # Border colors
                "border_light": "#cbd5e0",  # More visible light borders
                "border_medium": "#94a3b8",  # Medium borders
                "border_dark": "#64748b",  # Dark borders
                "border_focus": "#1d4ed8",  # Focus border color
                # Status colors (compliance focused)
                "success": "#059669",  # High confidence/good
                "warning": "#d97706",  # Medium confidence/caution
                "error": "#dc2626",  # Low confidence/issues
                "info": "#1d4ed8",  # Information
                # Accent colors
                "accent_1": "#7c3aed",  # Purple accent
                "accent_2": "#0891b2",  # Cyan accent
            },
            "dark": {
                # Primary medical colors (adjusted for dark theme)
                "primary_blue": "#3b82f6",  # Brighter medical blue
                "primary_green": "#10b981",  # Brighter medical green
                "kiro_black": "#475569",  # Lighter Kiro brand black
                "medical_gray": "#94a3b8",  # Lighter professional gray
                # Background colors
                "bg_primary": "#0f172a",  # Main dark background
                "bg_secondary": "#1e293b",  # Secondary dark background
                "bg_tertiary": "#334155",  # Tertiary dark background
                "bg_card": "#1e293b",  # Card background
                "bg_hover": "#334155",  # Hover background
                # Text colors
                "text_primary": "#f8fafc",  # Brighter main light text
                "text_secondary": "#e2e8f0",  # Brighter secondary light text
                "text_muted": "#94a3b8",  # Muted light text
                "text_inverse": "#0f172a",  # Dark text for light backgrounds
                # Border colors
                "border_light": "#334155",  # Light borders
                "border_medium": "#475569",  # Medium borders
                "border_dark": "#64748b",  # Dark borders
                "border_focus": "#3b82f6",  # Focus border color
                # Status colors (compliance focused)
                "success": "#22c55e",  # High confidence/good
                "warning": "#fbbf24",  # Medium confidence/caution
                "error": "#f87171",  # Low confidence/issues
                "info": "#60a5fa",  # Information
                # Accent colors
                "accent_1": "#a78bfa",  # Purple accent
                "accent_2": "#22d3ee",  # Cyan accent
            },
        }

    def get_color(self, color_name: str) -> str:
        """Get color value for current theme."""
        return self.colors[self.current_theme].get(color_name, "#000000")

    def set_theme(self, theme: str):
        """Set the current theme (light/dark)."""
        if theme in ["light", "dark"]:
            self.current_theme = theme
            self.theme_changed.emit(theme)

    def toggle_theme(self):
        """Toggle between light and dark theme."""
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.set_theme(new_theme)

    def get_main_window_stylesheet(self) -> str:
        """Get main window stylesheet for current theme."""
        colors = self.colors[self.current_theme]

        return f"""
        QMainWindow {{
            background-color: {colors["bg_primary"]};
            color: {colors["text_primary"]};
        }}
        
        QMenuBar {{
            background-color: {colors["bg_secondary"]};
            color: {colors["text_primary"]};
            border-bottom: 1px solid {colors["border_light"]};
            padding: 4px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 6px 12px;
            border-radius: 4px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors["primary_blue"]};
            color: white;
        }}
        
        QStatusBar {{
            background-color: {colors["bg_secondary"]};
            color: {colors["text_secondary"]};
            border-top: 1px solid {colors["border_light"]};
        }}
        
        QStatusBar QLabel#easter_egg {{
            font-family: "Brush Script MT", "Lucida Handwriting", cursive;
            font-size: 10px;
            color: {colors["text_muted"]};
            font-style: italic;
            opacity: 0.6;
        }}
        
        QTabWidget::pane {{
            border: 1px solid {colors["border_light"]};
            background-color: {colors["bg_primary"]};
        }}
        
        QTabBar::tab {{
            background-color: {colors["bg_secondary"]};
            color: {colors["text_secondary"]};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors["primary_blue"]};
            color: white;
        }}
        
        QTabBar::tab:hover {{
            background-color: {colors["border_medium"]};
        }}
        """

    def get_button_stylesheet(self, button_type: str = "primary") -> str:
        """Get button stylesheet for current theme."""
        colors = self.colors[self.current_theme]

        styles = {
            "primary": f"""
                QPushButton {{
                    background-color: {colors["primary_blue"]};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 500;
                    min-width: 80px;
                }}
                QPushButton:hover {{
                    background-color: {colors["kiro_black"]};
                }}
                QPushButton:pressed {{
                    background-color: {colors["medical_gray"]};
                }}
                QPushButton:disabled {{
                    background-color: {colors["border_medium"]};
                    color: {colors["text_muted"]};
                }}
            """,
            "secondary": f"""
                QPushButton {{
                    background-color: {colors["bg_secondary"]};
                    color: {colors["text_primary"]};
                    border: 1px solid {colors["border_medium"]};
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 500;
                    min-width: 80px;
                }}
                QPushButton:hover {{
                    background-color: {colors["bg_tertiary"]};
                    border-color: {colors["primary_blue"]};
                }}
                QPushButton:pressed {{
                    background-color: {colors["border_light"]};
                }}
            """,
            "success": f"""
                QPushButton {{
                    background-color: {colors["success"]};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 500;
                    min-width: 80px;
                }}
                QPushButton:hover {{
                    background-color: {colors["primary_green"]};
                }}
            """,
            "warning": f"""
                QPushButton {{
                    background-color: {colors["warning"]};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 500;
                    min-width: 80px;
                }}
            """,
            "danger": f"""
                QPushButton {{
                    background-color: {colors["error"]};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 500;
                    min-width: 80px;
                }}
            """,
        }

        return styles.get(button_type, styles["primary"])

    def get_card_stylesheet(self) -> str:
        """Get card stylesheet for current theme."""
        colors = self.colors[self.current_theme]

        return f"""
        QFrame {{
            background-color: {colors["bg_card"]};
            border: 1px solid {colors["border_light"]};
            border-radius: 8px;
            padding: 12px;
        }}
        
        QGroupBox {{
            background-color: {colors["bg_card"]};
            border: 1px solid {colors["border_light"]};
            border-radius: 8px;
            margin-top: 12px;
            font-weight: 600;
            color: {colors["text_primary"]};
            padding-top: 16px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            background-color: {colors["bg_card"]};
            color: {colors["primary_blue"]};
            font-size: 14px;
            font-weight: 600;
        }}
        """

    def get_form_stylesheet(self) -> str:
        """Get form input stylesheet for current theme."""
        colors = self.colors[self.current_theme]

        return f"""
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {colors["bg_primary"]};
            border: 2px solid {colors["border_light"]};
            border-radius: 6px;
            padding: 8px 12px;
            color: {colors["text_primary"]};
            font-size: 14px;
            min-height: 20px;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {colors["border_focus"]};
            background-color: {colors["bg_primary"]};
        }}
        
        QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {{
            border-color: {colors["border_medium"]};
        }}
        
        QComboBox {{
            background-color: {colors["bg_primary"]};
            border: 2px solid {colors["border_light"]};
            border-radius: 6px;
            padding: 8px 12px;
            color: {colors["text_primary"]};
            font-size: 14px;
            min-height: 20px;
            min-width: 120px;
        }}
        
        QComboBox:focus {{
            border-color: {colors["border_focus"]};
        }}
        
        QComboBox:hover {{
            border-color: {colors["border_medium"]};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {colors["text_secondary"]};
            margin-right: 5px;
        }}
        
        QSpinBox, QDoubleSpinBox {{
            background-color: {colors["bg_primary"]};
            border: 2px solid {colors["border_light"]};
            border-radius: 6px;
            padding: 8px 12px;
            color: {colors["text_primary"]};
            font-size: 14px;
            min-height: 20px;
        }}
        
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {colors["border_focus"]};
        }}
        
        QCheckBox {{
            color: {colors["text_primary"]};
            font-size: 14px;
            spacing: 8px;
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {colors["border_medium"]};
            border-radius: 4px;
            background-color: {colors["bg_primary"]};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {colors["primary_blue"]};
            border-color: {colors["primary_blue"]};
        }}
        
        QCheckBox::indicator:checked::after {{
            content: "✓";
            color: white;
            font-weight: bold;
        }}
        
        QSlider::groove:horizontal {{
            border: 1px solid {colors["border_light"]};
            height: 6px;
            background: {colors["bg_tertiary"]};
            border-radius: 3px;
        }}
        
        QSlider::handle:horizontal {{
            background: {colors["primary_blue"]};
            border: 2px solid {colors["primary_blue"]};
            width: 18px;
            height: 18px;
            margin: -7px 0;
            border-radius: 9px;
        }}
        
        QSlider::handle:horizontal:hover {{
            background: {colors["kiro_black"]};
            border-color: {colors["kiro_black"]};
        }}
        
        QLabel {{
            color: {colors["text_primary"]};
            font-size: 14px;
        }}
        """

    def get_tab_stylesheet(self) -> str:
        """Get tab widget stylesheet for current theme."""
        colors = self.colors[self.current_theme]

        return f"""
        QTabWidget::pane {{
            border: 1px solid {colors["border_light"]};
            background-color: {colors["bg_primary"]};
            border-radius: 8px;
        }}
        
        QTabBar::tab {{
            background-color: {colors["bg_secondary"]};
            color: {colors["text_secondary"]};
            padding: 12px 20px;
            margin-right: 2px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            min-width: 100px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors["primary_blue"]};
            color: {colors["text_inverse"]};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {colors["bg_hover"]};
            color: {colors["text_primary"]};
        }}
        """


# Global theme instance
medical_theme = MedicalTheme()
