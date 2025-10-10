"""Header Component - Reusable application header
Built with PySide6 (Official Qt for Python) for professional desktop UI
Provides consistent branding and controls across the application.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class HeaderComponent(QWidget):
    """Reusable header component with branding and theme controls.

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
        self.setFixedHeight(140)  # Larger height for title + description
        self.setObjectName("headerComponent")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 20, 15, 20)  # More vertical padding

        # Logo section (left - smaller)
        logo_section = self.create_logo_section()
        layout.addLayout(logo_section, stretch=0)

        # Title section (center - takes much more space)
        title_section = self.create_title_section()
        layout.addLayout(title_section, stretch=6)  # Much more space for title

        # Controls section (right - smaller)
        controls_section = self.create_controls_section()
        layout.addLayout(controls_section, stretch=0)

    def create_logo_section(self):
        """Create the logo section with professional medical icon."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 10, 0)  # Minimal margins

        # Professional medical compliance icon with easter egg
        self.icon_label = QLabel("📋")
        self.icon_label.setFont(QFont("Segoe UI", 32))  # Made bigger
        self.icon_label.setStyleSheet("""
            QLabel {
                color: #1d4ed8;
                background: rgba(29, 78, 216, 0.1);
                border-radius: 25px;
                padding: 12px;
                margin: 5px;
            }
            QLabel:hover {
                background: rgba(29, 78, 216, 0.2);
                transform: scale(1.05);
            }
        """)
        self.icon_label.setFixedSize(60, 60)  # Made bigger
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setToolTip("Therapy Compliance Analyzer - Click me!")
        self.icon_label.setCursor(Qt.CursorShape.PointingHandCursor)

        # Easter egg functionality
        self.icon_click_count = 0
        self.icon_label.mousePressEvent = self.on_icon_clicked

        layout.addWidget(self.icon_label)

        return layout

    def on_icon_clicked(self, event):
        """Handle icon clicks for easter egg functionality."""
        self.icon_click_count += 1

        if self.icon_click_count == 3:
            self.icon_label.setText("📊")
            self.icon_label.setToolTip("Keep clicking! You're getting warmer...")
        elif self.icon_click_count == 5:
            self.icon_label.setText("🎯")
            self.icon_label.setToolTip("Almost there! A few more clicks...")
        elif self.icon_click_count == 7:
            self.icon_label.setText("🎉")
            self.icon_label.setToolTip("Congratulations! You found the easter egg!")
            # Emit signal to parent if needed
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "🎉 Easter Egg Found!",
                "Congratulations! You discovered the hidden easter egg!\n\n"
                "🎯 You clicked the document icon 7 times!\n"
                "🌟 This shows attention to detail - a key skill for compliance!\n\n"
                "Keep up the great work! 🚀",
            )
            # Reset after showing message
            self.icon_click_count = 0
            self.icon_label.setText("📋")
            self.icon_label.setToolTip("Therapy Compliance Analyzer - Click me!")
        elif self.icon_click_count >= 10:
            # Reset if too many clicks
            self.icon_click_count = 0
            self.icon_label.setText("📋")
            self.icon_label.setToolTip("Therapy Compliance Analyzer - Click me!")

    def create_title_section(self):
        """Create the centered title section spanning the full width with large, bold text."""
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 15, 30, 15)
        layout.setSpacing(20)

        # Main title - large, bold, spanning full width
        self.title_label = QLabel("THERAPY REPORT COMPLIANCE ANALYSIS")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setFont(QFont("Segoe UI", 48, QFont.Weight.ExtraBold))  # Much larger and bolder
        self.title_label.setStyleSheet("""
            QLabel#titleLabel {
                color: #1d4ed8;
                text-align: center;
                padding: 25px 40px;
                background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
                border-radius: 20px;
                border: 3px solid #cbd5e0;
                font-weight: 900;
                letter-spacing: 2px;
                margin-bottom: 10px;
                min-height: 100px;
            }
        """)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setMinimumHeight(120)  # Taller for larger text
        layout.addWidget(self.title_label)

        # App description - large, bold, spanning full width
        self.description_label = QLabel("AI-Powered Clinical Documentation Analysis for Medicare Compliance")
        self.description_label.setObjectName("descriptionLabel")
        self.description_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))  # Much larger and bold
        self.description_label.setStyleSheet("""
            QLabel#descriptionLabel {
                color: #475569;
                text-align: center;
                padding: 18px 35px;
                background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                border-radius: 15px;
                border: 2px solid #e2e8f0;
                margin-top: 10px;
                font-weight: 700;
                letter-spacing: 1px;
                min-height: 60px;
            }
        """)
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description_label.setMinimumHeight(80)  # Taller for larger text
        layout.addWidget(self.description_label)

        return layout

    def create_controls_section(self):
        """Create the compact controls section."""
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 0, 0)  # Minimal margins

        # Theme toggle button - removed emoji as requested
        self.theme_button = QPushButton("Theme")
        self.theme_button.setObjectName("themeButton")
        self.theme_button.setFixedSize(70, 45)  # Wider for text
        self.theme_button.setToolTip("Toggle Dark/Light Theme (Ctrl+T)")
        self.theme_button.clicked.connect(self.on_theme_toggle)
        self.theme_button.setStyleSheet("""
            QPushButton#themeButton {
                background-color: #f1f5f9;
                border: 2px solid #cbd5e0;
                border-radius: 22px;
                font-size: 18px;
            }
            QPushButton#themeButton:hover {
                background-color: #e2e8f0;
                border-color: #1d4ed8;
            }
            QPushButton#themeButton:pressed {
                background-color: #cbd5e0;
            }
        """)

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
        self.description_label.setText(subtitle)

    def get_default_stylesheet(self):
        """Get the default stylesheet for the header."""
        return """
        #headerComponent {
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
        }

        #titleLabel {
            color: #4a90e2;
            font-weight: bold;
        }

        #titleLabel:hover {
            color: #357abd;
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
