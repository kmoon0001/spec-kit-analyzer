"""Contextual Help System - Provides tooltips and help bubbles throughout the UI.
Safe, optional feature that enhances user experience without affecting core functionality.
"""

import logging

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtWidgets import QDialog, QFrame, QLabel, QWidget

logger = logging.getLogger(__name__)


class HelpTooltip(QLabel):
    """Enhanced tooltip widget with rich text support and auto-positioning."""

    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.help_text = text
        self.setup_ui()

    def setup_ui(self):
        """Setup the tooltip appearance."""
        self.setWindowFlags(Qt.WindowType.ToolTip)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # Styling
        self.setStyleSheet(
            """
            QLabel {
                background-color: #ffffcc;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
                color: #333333;
                max-width: 300px;
            }
        """
        )

        self.setText(self.help_text)
        self.setWordWrap(True)
        self.adjustSize()

    def show_at_position(self, position: QPoint):
        """Show tooltip at specific position."""
        self.move(position)
        self.show()

        # Auto-hide after 5 seconds
        QTimer.singleShot(5000, self.hide)


class HelpBubble(QFrame):
    """Help bubble widget that can be embedded in the UI."""

    closed = Signal()

    def close_bubble(self):
        """Close the help bubble."""
        self.hide()
        self.closed.emit()


class ComplianceGuideDialog(QDialog):
    """Dialog showing embedded compliance guide and Medicare/CMS requirements."""

    def load_compliance_content(self):
        """Load compliance guide content."""
        content = """
        <h2>Physical Therapy Documentation Requirements</h2>

        <h3>Initial Evaluation Requirements</h3>
        <ul>
            <li><b>History:</b> Relevant medical history, onset of condition, prior therapy</li>
            <li><b>Systems Review:</b> Cardiovascular, musculoskeletal, neuromuscular, integumentary</li>
            <li><b>Tests and Measures:</b> Objective measurements and assessments</li>
            <li><b>Evaluation:</b> Clinical judgment and interpretation of findings</li>
            <li><b>Diagnosis:</b> Physical therapy diagnosis based on examination</li>
            <li><b>Prognosis:</b> Predicted level of improvement and time frame</li>
            <li><b>Plan of Care:</b> Goals, interventions, frequency, and duration</li>
        </ul>

        <h3>Progress Note Requirements</h3>
        <ul>
            <li><b>Subjective:</b> Patient's report of symptoms and functional status</li>
            <li><b>Objective:</b> Measurable findings from examination and treatment</li>
            <li><b>Assessment:</b> Progress toward goals and response to treatment</li>
            <li><b>Plan:</b> Modifications to treatment plan and next steps</li>
        </ul>

        <h3>Medicare Documentation Standards</h3>
        <ul>
            <li>Documentation must be legible and complete</li>
            <li>Each entry must be dated and signed</li>
            <li>Progress must be clearly documented</li>
            <li>Functional outcomes must be measurable</li>
            <li>Medical necessity must be established and maintained</li>
        </ul>

        <h3>Common Documentation Errors</h3>
        <ul>
            <li>Vague or subjective language without objective measures</li>
            <li>Missing or incomplete assessment of progress</li>
            <li>Lack of functional outcome measures</li>
            <li>Insufficient justification for continued treatment</li>
            <li>Missing physician orders or referrals</li>
        </ul>

        <h3>Best Practices</h3>
        <ul>
            <li>Use specific, measurable language</li>
            <li>Document functional improvements clearly</li>
            <li>Include patient response to treatment</li>
            <li>Justify medical necessity for each visit</li>
            <li>Update goals based on patient progress</li>
        </ul>

        <p><i>This guide provides general information and should not replace professional training or official CMS guidelines.</i></p>
        """

        self.content_area.setHtml(content)


class HelpSystem:
    """Main help system coordinator that manages contextual help throughout the application."""

    def _load_help_content(self) -> dict[str, dict[str, str]]:
        """Load help content for different UI elements."""
        return {
            "upload_button": {
                "title": "Document Upload",
                "content": "Upload PDF, DOCX, or TXT files for compliance analysis. Scanned documents will be processed with OCR.",
            },
            "rubric_selector": {
                "title": "Compliance Rubric",
                "content": "Select the appropriate compliance rubric for your discipline (PT, OT, SLP) to ensure accurate analysis.",
            },
            "analyze_button": {
                "title": "Run Analysis",
                "content": "Start AI-powered compliance analysis. This may take 30-60 seconds depending on document size.",
            },
            "compliance_score": {
                "title": "Compliance Score",
                "content": "Overall compliance score from 0-100%. Scores above 85% indicate good compliance.",
            },
            "findings_table": {
                "title": "Compliance Findings",
                "content": "Detailed list of compliance issues found in your document, with risk levels and recommendations.",
            },
            "performance_settings": {
                "title": "Performance Settings",
                "content": "Adjust system performance based on your hardware. Conservative mode for 6-8GB RAM, Aggressive for 12GB+.",
            },
            "dashboard": {
                "title": "Analytics Dashboard",
                "content": "View historical compliance trends, performance metrics, and insights from your analysis history.",
            },
        }

    def show_tooltip(self, widget: QWidget, help_key: str) -> bool:
        """Show contextual tooltip for a widget.

        Args:
            widget: Widget to show tooltip for
            help_key: Key to look up help content

        Returns:
            True if tooltip was shown, False otherwise

        """
        if not self.enabled:
            return False

        help_info = self.help_content.get(help_key)
        if not help_info:
            logger.warning("No help content found for key: %s", help_key)
            return False

        try:
            # Create tooltip
            tooltip_text = f"<b>{help_info['title']}</b><br><br>{help_info['content']}"
            parent_widget = widget.parent()
            tooltip = HelpTooltip(tooltip_text, parent_widget if isinstance(parent_widget, QWidget) else None)

            # Position tooltip near widget
            widget_pos = widget.mapToGlobal(QPoint(0, widget.height() + 5))
            tooltip.show_at_position(widget_pos)

            # Track active tooltip
            self.active_tooltips.append(tooltip)

            return True

        except (RuntimeError, AttributeError) as e:
            logger.exception("Error showing tooltip: %s", e)
            return False

    def show_help_bubble(self, parent: QWidget, help_key: str) -> HelpBubble | None:
        """Show help bubble widget that can be embedded in UI.

        Args:
            parent: Parent widget for the bubble
            help_key: Key to look up help content

        Returns:
            HelpBubble widget if created, None otherwise

        """
        if not self.enabled:
            return None

        help_info = self.help_content.get(help_key)
        if not help_info:
            return None

        try:
            bubble = HelpBubble(help_info["title"], help_info["content"], parent)
            bubble.closed.connect(lambda: self._remove_bubble(bubble))

            self.active_bubbles.append(bubble)
            return bubble

        except Exception as e:
            logger.exception("Error creating help bubble: %s", e)
            return None

    def show_compliance_guide(self, parent: QWidget | None = None) -> None:
        """Show the comprehensive compliance guide dialog."""
        if not self.enabled:
            return

        try:
            guide = ComplianceGuideDialog(parent)
            guide.show()
        except (RuntimeError, AttributeError) as e:
            logger.exception("Error showing compliance guide: %s", e)

    def _remove_bubble(self, bubble: HelpBubble):
        """Remove bubble from active list."""
        if bubble in self.active_bubbles:
            self.active_bubbles.remove(bubble)

    def cleanup(self):
        """Clean up active help elements."""
        for tooltip in self.active_tooltips:
            tooltip.hide()
        self.active_tooltips.clear()

        for bubble in self.active_bubbles:
            bubble.hide()
        self.active_bubbles.clear()

    def is_enabled(self) -> bool:
        """Check if help system is enabled."""
        return self.enabled

    def set_enabled(self, enabled: bool):
        """Enable or disable help system."""
        self.enabled = enabled
        if not enabled:
            self.cleanup()


# Global help system instance
# Global help system instance
# Global help system instance
help_system = HelpSystem()


def get_help_system(enabled: bool = True) -> HelpSystem:
    """Get help system instance with specified configuration."""
    return HelpSystem(enabled=enabled)


# Configuration
# Configuration
# Configuration
HELP_SYSTEM_CONFIG = {
    "enabled": True,
    "show_tooltips": True,
    "show_bubbles": True,
    "auto_show_guide": False,  # Whether to show guide on first run
}


def is_help_enabled() -> bool:
    """Check if help system is enabled."""
    return HELP_SYSTEM_CONFIG.get("enabled", True)
