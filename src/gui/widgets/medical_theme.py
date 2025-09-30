"""
Medical Theme System - Professional medical UI styling with light/dark themes.
"""
from PyQt6.QtCore import QObject, pyqtSignal

class MedicalTheme(QObject):
    """Medical theme manager with light/dark mode support."""

    theme_changed = pyqtSignal(str)  # Emits 'light' or 'dark'

    def __init__(self):
        super().__init__()
        self.current_theme = 'light'

        # Medical color palette
        self.colors = {
            'light': {
                # Primary medical colors
                'primary_blue': '#2563eb',      # Medical blue
                'primary_green': '#059669',     # Medical green
                'kiro_black': '#1e293b',        # Kiro brand black
                'medical_gray': '#64748b',      # Professional gray

                # Background colors
                'bg_primary': '#ffffff',        # Main background
                'bg_secondary': '#f8fafc',      # Secondary background
                'bg_tertiary': '#f1f5f9',       # Tertiary background

                # Text colors
                'text_primary': '#1e293b',      # Main text
                'text_secondary': '#475569',    # Secondary text
                'text_muted': '#94a3b8',        # Muted text

                # Border colors
                'border_light': '#e2e8f0',      # Light borders
                'border_medium': '#cbd5e0',     # Medium borders
                'border_dark': '#94a3b8',       # Dark borders

                # Status colors (compliance focused)
                'success': '#10b981',           # High confidence/good
                'warning': '#f59e0b',           # Medium confidence/caution
                'error': '#ef4444',             # Low confidence/issues
                'info': '#3b82f6',              # Information

                # Accent colors
                'accent_1': '#8b5cf6',          # Purple accent
                'accent_2': '#06b6d4',          # Cyan accent
            },
            'dark': {
                # Primary medical colors (adjusted for dark theme)
                'primary_blue': '#3b82f6',      # Brighter medical blue
                'primary_green': '#10b981',     # Brighter medical green
                'kiro_black': '#374151',        # Lighter Kiro brand black
                'medical_gray': '#94a3b8',      # Lighter professional gray

                # Background colors
                'bg_primary': '#0f172a',        # Main dark background
                'bg_secondary': '#1e293b',      # Secondary dark background
                'bg_tertiary': '#334155',       # Tertiary dark background

                # Text colors
                'text_primary': '#f1f5f9',      # Main light text
                'text_secondary': '#cbd5e0',    # Secondary light text
                'text_muted': '#64748b',        # Muted light text

                # Border colors
                'border_light': '#334155',      # Light borders
                'border_medium': '#475569',     # Medium borders
                'border_dark': '#64748b',       # Dark borders

                # Status colors (compliance focused)
                'success': '#22c55e',           # High confidence/good
                'warning': '#fbbf24',           # Medium confidence/caution
                'error': '#f87171',             # Low confidence/issues
                'info': '#60a5fa',              # Information

                # Accent colors
                'accent_1': '#a78bfa',          # Purple accent
                'accent_2': '#22d3ee',          # Cyan accent
            }
        }

    def get_color(self, color_name: str) -> str:
        """Get color value for current theme."""
        return self.colors[self.current_theme].get(color_name, '#000000')

    def set_theme(self, theme: str):
        """Set the current theme (light/dark)."""
        if theme in ['light', 'dark']:
            self.current_theme = theme
            self.theme_changed.emit(theme)

    def toggle_theme(self):
        """Toggle between light and dark theme."""
        new_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.set_theme(new_theme)

    def get_main_window_stylesheet(self) -> str:
        """Get main window stylesheet for current theme."""
        colors = self.colors[self.current_theme]

        return f"""
        QMainWindow {{
            background-color: {colors['bg_primary']};
            color: {colors['text_primary']};
        }}
        
        QMenuBar {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_primary']};
            border-bottom: 1px solid {colors['border_light']};
            padding: 4px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 6px 12px;
            border-radius: 4px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors['primary_blue']};
            color: white;
        }}
        
        QStatusBar {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_secondary']};
            border-top: 1px solid {colors['border_light']};
        }}
        
        QStatusBar QLabel#easter_egg {{
            font-family: "Brush Script MT", "Lucida Handwriting", cursive;
            font-size: 10px;
            color: {colors['text_muted']};
            font-style: italic;
            opacity: 0.6;
        }}
        
        QTabWidget::pane {{
            border: 1px solid {colors['border_light']};
            background-color: {colors['bg_primary']};
        }}
        
        QTabBar::tab {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_secondary']};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors['primary_blue']};
            color: white;
        }}
        
        QTabBar::tab:hover {{
            background-color: {colors['border_medium']};
        }}
        """

    def get_button_stylesheet(self, button_type: str = 'primary') -> str:
        """Get button stylesheet for current theme."""
        colors = self.colors[self.current_theme]

        styles = {
            'primary': f"""
                QPushButton {{
                    background-color: {colors['primary_blue']};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 500;
                    min-width: 80px;
                }}
                QPushButton:hover {{
                    background-color: {colors['kiro_black']};
                }}
                QPushButton:pressed {{
                    background-color: {colors['medical_gray']};
                }}
                QPushButton:disabled {{
                    background-color: {colors['border_medium']};
                    color: {colors['text_muted']};
                }}
            """,
            'secondary': f"""
                QPushButton {{
                    background-color: {colors['bg_secondary']};
                    color: {colors['text_primary']};
                    border: 1px solid {colors['border_medium']};
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 500;
                    min-width: 80px;
                }}
                QPushButton:hover {{
                    background-color: {colors['bg_tertiary']};
                    border-color: {colors['primary_blue']};
                }}
                QPushButton:pressed {{
                    background-color: {colors['border_light']};
                }}
            """,
            'success': f"""
                QPushButton {{
                    background-color: {colors['success']};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 500;
                    min-width: 80px;
                }}
                QPushButton:hover {{
                    background-color: {colors['primary_green']};
                }}
            """,
            'warning': f"""
                QPushButton {{
                    background-color: {colors['warning']};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 500;
                    min-width: 80px;
                }}
            """,
            'danger': f"""
                QPushButton {{
                    background-color: {colors['error']};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 500;
                    min-width: 80px;
                }}
            """
        }

        return styles.get(button_type, styles['primary'])

    def get_card_stylesheet(self) -> str:
        """Get card stylesheet for current theme."""
        colors = self.colors[self.current_theme]

        return f"""
        QFrame {{
            background-color: {colors['bg_primary']};
            border: 1px solid {colors['border_light']};
            border-radius: 8px;
        }}
        
        QGroupBox {{
            background-color: {colors['bg_primary']};
            border: 1px solid {colors['border_light']};
            border-radius: 8px;
            margin-top: 12px;
            font-weight: 600;
            color: {colors['text_primary']};
            padding-top: 8px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            background-color: {colors['bg_primary']};
            color: {colors['primary_blue']};
        }}
        """

# Global theme instance
medical_theme = MedicalTheme()
