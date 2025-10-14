"""
PyCharm Dark Theme for PySide6

Complete PyCharm-inspired dark theme with:
    - Consistent color palette
    - Professional styling
    - No light/white elements
    - Button-icon lighting for status (no dots!)
    - Subtle animations and effects
"""

from typing import Dict


# PyCharm Dark Color Palette
PYCHARM_COLORS: Dict[str, str] = {
    # Base colors
    'background': '#2B2B2B',        # Main background
    'background_light': '#3A3A3A',  # Lighter background for panels
    'background_dark': '#1E1E1E',   # Darker background for contrast
    
    # Text colors
    'foreground': '#A9B7C6',        # Primary text
    'foreground_dim': '#808080',    # Dimmed/disabled text
    'foreground_bright': '#D0D0D0', # Bright text for emphasis
    
    # Accent colors
    'accent': '#4A9FD8',            # Primary accent (blue)
    'accent_hover': '#5BA3E0',      # Accent hover state
    'accent_pressed': '#3A8DC8',    # Accent pressed state
    
    # Status colors
    'success': '#6A8759',           # Green for success
    'error': '#FF6B68',             # Red for errors
    'warning': '#FFC66D',           # Orange/yellow for warnings
    'info': '#4A9FD8',              # Blue for info
    
    # Border and separator
    'border': '#323232',            # Default borders
    'border_light': '#4D4D4D',      # Lighter borders
    'separator': '#282828',         # Separators/dividers
    
    # Interactive states
    'hover': '#3A3A3A',             # Hover background
    'selected': '#214283',          # Selected item background
    'pressed': '#1A1A1A',           # Pressed state
    
    # Scrollbar
    'scrollbar_bg': '#2B2B2B',      # Scrollbar background
    'scrollbar_handle': '#4D4D4D',  # Scrollbar handle
    'scrollbar_hover': '#5D5D5D',   # Scrollbar hover
    
    # Input fields
    'input_bg': '#3A3A3A',          # Input background
    'input_border': '#4D4D4D',      # Input border
    'input_focus': '#4A9FD8',       # Input focus border
}


class PyCharmDarkTheme:
    """
    PyCharm Dark Theme manager.
    
    Provides:
        - Complete stylesheet generation
        - Component-specific styles
        - Consistent color palette
        - Professional appearance
    
    Usage:
        ```python
        theme = PyCharmDarkTheme()
        
        # Apply to entire app
        app.setStyleSheet(theme.get_application_stylesheet())
        
        # Get specific button style
        button.setStyleSheet(theme.get_button_stylesheet("primary"))
        ```
    """
    
    def __init__(self):
        """Initialize theme."""
        self.colors = PYCHARM_COLORS
    
    def get_application_stylesheet(self) -> str:
        """
        Get complete application stylesheet.
        
        Returns:
            Complete QSS stylesheet string
        """
        return f"""
        /* === GLOBAL APPLICATION STYLE === */
        QWidget {{
            background-color: {self.colors['background']};
            color: {self.colors['foreground']};
            font-family: 'Segoe UI', 'San Francisco', Arial, sans-serif;
            font-size: 12px;
        }}
        
        /* === MAIN WINDOW === */
        QMainWindow {{
            background-color: {self.colors['background']};
        }}
        
        /* === TAB WIDGET === */
        QTabWidget::pane {{
            border: 1px solid {self.colors['border']};
            background: {self.colors['background']};
        }}
        
        QTabBar::tab {{
            background: {self.colors['background_light']};
            color: {self.colors['foreground']};
            border: 1px solid {self.colors['border']};
            border-bottom: none;
            padding: 8px 16px;
            margin-right: 2px;
        }}
        
        QTabBar::tab:selected {{
            background: {self.colors['selected']};
            color: {self.colors['foreground_bright']};
            border-bottom: 2px solid {self.colors['accent']};
        }}
        
        QTabBar::tab:hover {{
            background: {self.colors['hover']};
        }}
        
        /* === BUTTONS === */
        QPushButton {{
            background: {self.colors['background_light']};
            color: {self.colors['foreground']};
            border: 1px solid {self.colors['border']};
            border-radius: 4px;
            padding: 8px 16px;
            min-height: 30px;
        }}
        
        QPushButton:hover {{
            background: {self.colors['hover']};
            border-color: {self.colors['border_light']};
        }}
        
        QPushButton:pressed {{
            background: {self.colors['pressed']};
        }}
        
        QPushButton:disabled {{
            background: {self.colors['background_dark']};
            color: {self.colors['foreground_dim']};
            border-color: {self.colors['border']};
        }}
        
        /* === TEXT INPUTS === */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background: {self.colors['input_bg']};
            color: {self.colors['foreground']};
            border: 1px solid {self.colors['input_border']};
            border-radius: 4px;
            padding: 6px;
            selection-background-color: {self.colors['selected']};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {self.colors['input_focus']};
        }}
        
        /* === COMBO BOX === */
        QComboBox {{
            background: {self.colors['input_bg']};
            color: {self.colors['foreground']};
            border: 1px solid {self.colors['input_border']};
            border-radius: 4px;
            padding: 6px;
        }}
        
        QComboBox:hover {{
            border-color: {self.colors['border_light']};
        }}
        
        QComboBox:focus {{
            border-color: {self.colors['input_focus']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: url(none);  /* Remove default arrow */
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid {self.colors['foreground']};
            margin-right: 6px;
        }}
        
        QComboBox QAbstractItemView {{
            background: {self.colors['background_light']};
            color: {self.colors['foreground']};
            border: 1px solid {self.colors['border']};
            selection-background-color: {self.colors['selected']};
        }}
        
        /* === LIST WIDGET === */
        QListWidget {{
            background: {self.colors['background']};
            color: {self.colors['foreground']};
            border: 1px solid {self.colors['border']};
            border-radius: 4px;
        }}
        
        QListWidget::item {{
            padding: 6px;
        }}
        
        QListWidget::item:selected {{
            background: {self.colors['selected']};
        }}
        
        QListWidget::item:hover {{
            background: {self.colors['hover']};
        }}
        
        /* === SCROLL BAR === */
        QScrollBar:vertical {{
            background: {self.colors['scrollbar_bg']};
            width: 12px;
            border: none;
        }}
        
        QScrollBar::handle:vertical {{
            background: {self.colors['scrollbar_handle']};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {self.colors['scrollbar_hover']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background: {self.colors['scrollbar_bg']};
            height: 12px;
            border: none;
        }}
        
        QScrollBar::handle:horizontal {{
            background: {self.colors['scrollbar_handle']};
            border-radius: 6px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background: {self.colors['scrollbar_hover']};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        
        /* === PROGRESS BAR === */
        QProgressBar {{
            background: {self.colors['background_light']};
            border: 1px solid {self.colors['border']};
            border-radius: 4px;
            text-align: center;
            color: {self.colors['foreground']};
        }}
        
        QProgressBar::chunk {{
            background: {self.colors['accent']};
            border-radius: 3px;
        }}
        
        /* === GROUP BOX === */
        QGroupBox {{
            background: {self.colors['background']};
            border: 1px solid {self.colors['border']};
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 10px;
            font-weight: bold;
        }}
        
        QGroupBox::title {{
            color: {self.colors['accent']};
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
        }}
        
        /* === STATUS BAR === */
        QStatusBar {{
            background: {self.colors['background']};
            color: {self.colors['foreground']};
            border-top: 1px solid {self.colors['border']};
        }}
        
        /* === MENU BAR === */
        QMenuBar {{
            background: {self.colors['background_light']};
            color: {self.colors['foreground']};
            border-bottom: 1px solid {self.colors['border']};
        }}
        
        QMenuBar::item {{
            padding: 6px 12px;
            background: transparent;
        }}
        
        QMenuBar::item:selected {{
            background: {self.colors['hover']};
        }}
        
        QMenu {{
            background: {self.colors['background_light']};
            color: {self.colors['foreground']};
            border: 1px solid {self.colors['border']};
        }}
        
        QMenu::item {{
            padding: 6px 24px;
        }}
        
        QMenu::item:selected {{
            background: {self.colors['selected']};
        }}
        
        /* === TOOLTIPS === */
        QToolTip {{
            background: {self.colors['background_light']};
            color: {self.colors['foreground']};
            border: 1px solid {self.colors['border']};
            padding: 4px;
            border-radius: 4px;
        }}
        
        /* === CHECKBOX & RADIO === */
        QCheckBox, QRadioButton {{
            color: {self.colors['foreground']};
            spacing: 8px;
        }}
        
        QCheckBox:disabled, QRadioButton:disabled {{
            color: {self.colors['foreground_dim']};
        }}
        
        /* === LABEL === */
        QLabel {{
            color: {self.colors['foreground']};
            background: transparent;
        }}
        """
    
    def get_button_stylesheet(self, button_type: str = "primary") -> str:
        """
        Get button stylesheet for specific type.
        
        Args:
            button_type: Button type ("primary", "success", "error", "warning", "secondary")
            
        Returns:
            QSS stylesheet string
        """
        styles = {
            "primary": f"""
                QPushButton {{
                    background: {self.colors['accent']};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 4px;
                    padding: 10px 20px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: {self.colors['accent_hover']};
                }}
                QPushButton:pressed {{
                    background: {self.colors['accent_pressed']};
                }}
                QPushButton:disabled {{
                    background: {self.colors['background_light']};
                    color: {self.colors['foreground_dim']};
                }}
            """,
            "success": f"""
                QPushButton {{
                    background: {self.colors['success']};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 4px;
                    padding: 10px 20px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: #7A9769;
                }}
                QPushButton:disabled {{
                    background: {self.colors['background_light']};
                    color: {self.colors['foreground_dim']};
                }}
            """,
            "error": f"""
                QPushButton {{
                    background: {self.colors['error']};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 4px;
                    padding: 10px 20px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: #FF7B78;
                }}
                QPushButton:disabled {{
                    background: {self.colors['background_light']};
                    color: {self.colors['foreground_dim']};
                }}
            """,
            "warning": f"""
                QPushButton {{
                    background: {self.colors['warning']};
                    color: #2B2B2B;
                    border: none;
                    border-radius: 4px;
                    padding: 10px 20px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: #FFD07D;
                }}
                QPushButton:disabled {{
                    background: {self.colors['background_light']};
                    color: {self.colors['foreground_dim']};
                }}
            """,
            "secondary": f"""
                QPushButton {{
                    background: {self.colors['background_light']};
                    color: {self.colors['foreground']};
                    border: 1px solid {self.colors['border']};
                    border-radius: 4px;
                    padding: 10px 20px;
                }}
                QPushButton:hover {{
                    background: {self.colors['hover']};
                    border-color: {self.colors['border_light']};
                }}
                QPushButton:disabled {{
                    background: {self.colors['background_dark']};
                    color: {self.colors['foreground_dim']};
                }}
            """
        }
        
        return styles.get(button_type, styles["primary"])
    
    def get_status_indicator_stylesheet(self, status: str = "normal") -> str:
        """
        Get status indicator stylesheet (button-icon lighting style, NO DOTS!).
        
        Args:
            status: Status type ("normal", "success", "error", "warning")
            
        Returns:
            QSS stylesheet string
        """
        styles = {
            "success": f"""
                QLabel {{
                    color: {self.colors['success']};
                    background: rgba(106, 135, 89, 0.2);
                    border: 1px solid {self.colors['success']};
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-weight: bold;
                }}
            """,
            "error": f"""
                QLabel {{
                    color: {self.colors['error']};
                    background: rgba(255, 107, 104, 0.2);
                    border: 1px solid {self.colors['error']};
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-weight: bold;
                }}
            """,
            "warning": f"""
                QLabel {{
                    color: {self.colors['warning']};
                    background: rgba(255, 198, 109, 0.2);
                    border: 1px solid {self.colors['warning']};
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-weight: bold;
                }}
            """,
            "normal": f"""
                QLabel {{
                    color: {self.colors['foreground']};
                    background: rgba(169, 183, 198, 0.1);
                    border: 1px solid {self.colors['border']};
                    border-radius: 4px;
                    padding: 4px 10px;
                }}
            """
        }
        
        return styles.get(status, styles["normal"])


# Global theme instance
pycharm_theme = PyCharmDarkTheme()

