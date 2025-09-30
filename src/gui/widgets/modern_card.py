"""
Modern Card Widget - Clean cards with shadows and medical styling.
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette

class ModernCard(QFrame):
    """Modern card widget with shadow and clean styling."""

    clicked = pyqtSignal()

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.setup_ui()
        self.apply_card_style()

    def setup_ui(self):
        """Setup the card UI structure."""
        self.setFrameStyle(QFrame.Shape.NoFrame)

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 12, 16, 12)
        self.main_layout.setSpacing(8)

        # Header layout (title + optional controls)
        if self.title:
            self.header_layout = QHBoxLayout()

            # Title label
            self.title_label = QLabel(self.title)
            title_font = QFont()
            title_font.setPointSize(11)
            title_font.setWeight(QFont.Weight.DemiBold)
            self.title_label.setFont(title_font)
            self.title_label.setStyleSheet("color: #2c5282; margin-bottom: 4px;")

            self.header_layout.addWidget(self.title_label)
            self.header_layout.addStretch()

            self.main_layout.addLayout(self.header_layout)

        # Content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.content_widget)

    def apply_card_style(self):
        """Apply modern card styling with shadow effect."""
        self.setStyleSheet("""
            ModernCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                margin: 4px;
            }
            ModernCard:hover {
                border-color: #cbd5e0;
                background-color: #f8fafc;
            }
        """)

        # Add shadow effect
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

    def add_content(self, widget: QWidget):
        """Add content to the card."""
        self.content_layout.addWidget(widget)

    def set_status_color(self, status: str):
        """Set card border color based on status."""
        colors = {
            'success': '#10b981',  # Green
            'warning': '#f59e0b',  # Yellow
            'error': '#ef4444',    # Red
            'info': '#3b82f6',     # Blue
            'default': '#e2e8f0'   # Gray
        }

        color = colors.get(status, colors['default'])
        self.setStyleSheet(f"""
            ModernCard {{
                background-color: #ffffff;
                border: 2px solid {color};
                border-radius: 8px;
                margin: 4px;
            }}
        """)

class ComplianceCard(ModernCard):
    """Specialized card for compliance results with color coding."""

    def __init__(self, title: str = "", confidence: float = 0.0, parent=None):
        super().__init__(title, parent)
        self.confidence = confidence
        self.setup_compliance_ui()

    def setup_compliance_ui(self):
        """Setup compliance-specific UI elements."""
        # Confidence indicator
        confidence_layout = QHBoxLayout()

        confidence_label = QLabel("Confidence:")
        confidence_label.setStyleSheet("font-size: 10px; color: #64748b;")

        self.confidence_value = QLabel(f"{self.confidence:.1%}")
        self.confidence_value.setStyleSheet("font-size: 10px; font-weight: bold;")

        # Color code based on confidence
        if self.confidence >= 0.8:
            self.confidence_value.setStyleSheet("font-size: 10px; font-weight: bold; color: #10b981;")
            self.set_status_color('success')
        elif self.confidence >= 0.6:
            self.confidence_value.setStyleSheet("font-size: 10px; font-weight: bold; color: #f59e0b;")
            self.set_status_color('warning')
        else:
            self.confidence_value.setStyleSheet("font-size: 10px; font-weight: bold; color: #ef4444;")
            self.set_status_color('error')

        confidence_layout.addWidget(confidence_label)
        confidence_layout.addWidget(self.confidence_value)
        confidence_layout.addStretch()

        if self.title:
            self.header_layout.addLayout(confidence_layout)

    def update_confidence(self, confidence: float):
        """Update confidence value and styling."""
        self.confidence = confidence
        self.confidence_value.setText(f"{confidence:.1%}")

        # Update color coding
        if confidence >= 0.8:
            self.confidence_value.setStyleSheet("font-size: 10px; font-weight: bold; color: #10b981;")
            self.set_status_color('success')
        elif confidence >= 0.6:
            self.confidence_value.setStyleSheet("font-size: 10px; font-weight: bold; color: #f59e0b;")
            self.set_status_color('warning')
        else:
            self.confidence_value.setStyleSheet("font-size: 10px; font-weight: bold; color: #ef4444;")
            self.set_status_color('error')