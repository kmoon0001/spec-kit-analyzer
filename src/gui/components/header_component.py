"""
Header Component - Reusable application header
Provides consistent branding and controls across the application.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame


class HeaderComponent(QWidget):
    """
    Reusable header component with branding and theme controls.
    
    Signals:
        theme_toggle_requested: Emitted when user requests theme toggle
        logo_clicked: Emitted when logo is clicked (for easter eggs)
    """
    
    theme_toggle_requested = Signal()
    logo_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.click_count = 0
        self.init_ui()
        
    def init_ui(self):
        """Initialize the header UI."""
        self.setFixedHeight(80)
        self.setObjectName("headerComponent")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Logo and title section
        title_section = self.create_title_section()
        layout.addLayout(title_section)
        
        # Spacer
        layout.addStretch()
        
        # Controls section
        controls_section = self.create_controls_section()
        layout.addLayout(controls_section)
        
    def create_title_section(self):
        """Create the title and logo section."""
        layout = QVBoxLayout()
        
        # Main title (clickable for easter eggs)
        self.title_label = QLabel("🏥 Therapy Compliance Analyzer")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.title_label.mousePressEvent = self.on_logo_clicked
        self.title_label.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Subtitle
        self.subtitle_label = QLabel("AI-Powered Clinical Documentation Analysis")
        self.subtitle_label.setObjectName("subtitleLabel")
        self.subtitle_label.setFont(QFont("Segoe UI", 10))
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        
        return layout
        
    def create_controls_section(self):
        """Create the controls section."""
        layout = QHBoxLayout()
        
        # Theme toggle button
        self.theme_button = QPushButton("🌙")
        self.theme_button.setObjectName("themeButton")
        self.theme_button.setFixedSize(40, 40)
        self.theme_button.setToolTip("Toggle Dark/Light Theme")
        self.theme_button.clicked.connect(self.on_theme_toggle)
        
        layout.addWidget(self.theme_button)
        
        return layout
        
    def on_logo_clicked(self, event):
        """Handle logo clicks for easter eggs."""
        self.click_count += 1
        self.logo_clicked.emit()
        
        # Reset click count after 7 clicks
        if self.click_count >= 7:
            self.click_count = 0
            
    def on_theme_toggle(self):
        """Handle theme toggle request."""
        self.theme_toggle_requested.emit()
        
    def update_theme_button(self, is_dark_theme: bool):
        """Update theme button icon based on current theme."""
        if is_dark_theme:
            self.theme_button.setText("☀️")
            self.theme_button.setToolTip("Switch to Light Theme")
        else:
            self.theme_button.setText("🌙")
            self.theme_button.setToolTip("Switch to Dark Theme")
            
    def set_subtitle(self, subtitle: str):
        """Update the subtitle text."""
        self.subtitle_label.setText(subtitle)
        
    def get_default_stylesheet(self):
        """Get the default stylesheet for the header."""
        return """
        #headerComponent {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #4a90e2, stop:1 #357abd);
            border-radius: 10px;
        }
        
        #titleLabel {
            color: white;
        }
        
        #titleLabel:hover {
            color: #f0f0f0;
        }
        
        #subtitleLabel {
            color: rgba(255, 255, 255, 0.8);
        }
        
        #themeButton {
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 20px;
            color: white;
            font-size: 16px;
        }
        
        #themeButton:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        
        #themeButton:pressed {
            background: rgba(255, 255, 255, 0.1);
        }
        """
        
    def get_dark_theme_stylesheet(self):
        """Get the dark theme stylesheet for the header."""
        return """
        #headerComponent {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #3a3a3a, stop:1 #4a4a4a);
            border-radius: 10px;
        }
        
        #titleLabel {
            color: white;
        }
        
        #titleLabel:hover {
            color: #e0e0e0;
        }
        
        #subtitleLabel {
            color: rgba(255, 255, 255, 0.7);
        }
        
        #themeButton {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            color: white;
            font-size: 16px;
        }
        
        #themeButton:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        #themeButton:pressed {
            background: rgba(255, 255, 255, 0.05);
        }
        """