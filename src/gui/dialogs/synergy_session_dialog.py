"""
Synergy Session Dialog - A collaborative workspace for tackling complex
clinical documentation scenarios with AI assistance.
"""
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QGroupBox,
    QLabel,
    QSplitter,
)
from PyQt6.QtCore import Qt, QThread
from typing import Dict, Any

from ..workers.synergy_worker import SynergyWorker

class SynergySessionDialog(QDialog):
    """
    A dialog that provides a 'Synergy Board' for clinicians to work through
    complex cases with AI-powered suggestions and guidelines.
    """
    def __init__(self, token: str, parent=None):
        super().__init__(parent)
        self.token = token
        self.setWindowTitle("Synergy Session for Complex Cases")
        self.setMinimumSize(900, 700)
        self._init_ui()
        self.worker = None
        self.thread = None

    def _init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)

        # 1. Top section for user input
        input_group = QGroupBox("Describe the Complex Clinical Scenario")
        input_layout = QVBoxLayout(input_group)
        self.scenario_input = QTextEdit()
        self.scenario_input.setPlaceholderText(
            "Example: 'My patient has a rare neurological condition and standard goals are not applicable. "
            "How can I document medical necessity for a custom-fabricated orthosis when progress is slow?'"
        )
        self.scenario_input.setMinimumHeight(100)

        self.start_session_button = QPushButton("🚀 Start Synergy Session")
        self.start_session_button.setStyleSheet("padding: 8px; font-size: 14px;")

        input_layout.addWidget(self.scenario_input)
        input_layout.addWidget(self.start_session_button)
        main_layout.addWidget(input_group)

        # 2. Main content area (Synergy Board)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side: AI Suggestions
        suggestions_group = QGroupBox("AI-Generated Phrase Suggestions")
        suggestions_layout = QVBoxLayout(suggestions_group)
        self.suggestions_display = QTextEdit()
        self.suggestions_display.setReadOnly(True)
        suggestions_layout.addWidget(self.suggestions_display)

        # Right side: Guidelines and Rules
        guidelines_group = QGroupBox("Relevant Guidelines & Rules")
        guidelines_layout = QVBoxLayout(guidelines_group)
        self.guidelines_display = QTextEdit()
        self.guidelines_display.setReadOnly(True)
        guidelines_layout.addWidget(self.guidelines_display)

        splitter.addWidget(suggestions_group)
        splitter.addWidget(guidelines_group)
        splitter.setSizes([450, 450])

        main_layout.addWidget(splitter, 1)

        # Connections
        self.start_session_button.clicked.connect(self.run_synergy_session)

    def run_synergy_session(self):
        """Initiates the backend worker to get synergy data."""
        scenario = self.scenario_input.toPlainText().strip()
        if not scenario:
            return

        self.start_session_button.setEnabled(False)
        self.start_session_button.setText("🧠 Generating Synergy...")
        self.suggestions_display.setText("Thinking...")
        self.guidelines_display.setText("Retrieving...")

        self.thread = QThread()
        self.worker = SynergyWorker(scenario, self.token)
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.worker.success.connect(self.on_synergy_success)
        self.worker.error.connect(self.on_synergy_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def on_synergy_success(self, data: Dict[str, Any]):
        """Populates the board with data from the backend."""
        self.start_session_button.setEnabled(True)
        self.start_session_button.setText("🚀 Start Synergy Session")

        suggestions = data.get("suggestions", ["No suggestions generated."])
        self.suggestions_display.setHtml("<ul><li>" + "</li><li>".join(suggestions) + "</li></ul>")

        guidelines = data.get("guidelines", [])
        guidelines_html = ""
        for rule in guidelines:
            guidelines_html += f"<h4>{rule.get('name', 'N/A')}</h4><p>{rule.get('content', 'No content.')}</p><hr>"
        self.guidelines_display.setHtml(guidelines_html)

    def on_synergy_error(self, error: str):
        """Handles errors during the synergy session."""
        self.start_session_button.setEnabled(True)
        self.start_session_button.setText("🚀 Start Synergy Session")
        self.suggestions_display.setText(f"<font color='red'>Error: {error}</font>")
        self.guidelines_display.clear()

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    dialog = SynergySessionDialog(token="dummy_token")
    dialog.show()

    # Example of how to populate after a successful run
    example_data = {
        "suggestions": [
            "Patient requires custom-fabricated orthosis due to atypical anatomical presentation secondary to [Condition Name], which precludes the use of off-the-shelf devices.",
            "Slow progress is anticipated due to the chronic and degenerative nature of [Condition Name]; however, the orthosis is crucial for maintaining current functional level and preventing further decline.",
            "Medical necessity is established by the need to maximize patient's safe and independent mobility, reduce fall risk, and manage pain associated with the unique biomechanical challenges of their condition.",
        ],
        "guidelines": [
            {"name": "CMS Rule 123.45", "content": "Documentation for custom orthotics must clearly justify why a prefabricated device is not suitable for the patient's specific condition."},
            {"name": "Best Practice: Justifying Slow Progress", "content": "When progress is not the primary goal, documentation should focus on prevention of functional decline, safety, and pain management as key indicators of medical necessity."},
        ]
    }
    # dialog.on_synergy_success(example_data)

    sys.exit(app.exec())