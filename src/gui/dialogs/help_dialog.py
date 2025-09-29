from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton
from PyQt6.QtCore import Qt

class HelpDialog(QDialog):
    """
    A dialog that displays a helpful tutorial for using the application.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("? Help & Tutorial")
        self.setGeometry(200, 200, 700, 500)

        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #bbbbbb;
            }
            QTextBrowser {
                background-color: #3c3f41;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
            }
        """)

        layout = QVBoxLayout(self)

        self.help_content = QTextBrowser()
        self.help_content.setOpenExternalLinks(True)
        self.help_content.setHtml(self.get_help_html())
        layout.addWidget(self.help_content)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)

    def get_help_html(self) -> str:
        """
        Returns the HTML content for the help dialog.
        """
        return """
        <html>
        <body style="font-family: sans-serif; font-size: 14px; color: #dddddd; line-height: 1.6;">
            <h1 style="color: #4a90e2;">How to Use the Therapy Compliance Analyzer</h1>
            <p>
                This guide will walk you through the basic steps to analyze a clinical document for compliance.
            </p>

            <h2 style="color: #4a90e2; border-bottom: 1px solid #4a4a4a; padding-bottom: 5px;">Step 1: Select a Compliance Rubric</h2>
            <p>
                In the top-left section, use the <strong>"Compliance Rubric"</strong> dropdown menu to choose the set of guidelines you want to analyze against. The default is <em>"Medicare Part B Requirements,"</em> but you can also select discipline-specific rubrics.
            </p>

            <h2 style="color: #4a90e2; border-bottom: 1px solid #4a4a4a; padding-bottom: 5px;">Step 2: Upload a Document</h2>
            <p>
                In the top-right section, click the <strong>"Upload Document"</strong> button to select a clinical note from your computer. The application supports PDF, DOCX, and TXT files. Once uploaded, the file name will appear in the status area.
            </p>

            <h2 style="color: #4a90e2; border-bottom: 1px solid #4a4a4a; padding-bottom: 5px;">Step 3: Run the Analysis</h2>
            <p>
                Once a document is uploaded, the <strong>"Run Analysis"</strong> button will become active. Click it to begin the AI analysis. The progress bar will show the real-time status of the analysis.
            </p>

            <h2 style="color: #4a90e2; border-bottom: 1px solid #4a4a4a; padding-bottom: 5px;">Step 4: Review the Results</h2>
            <p>
                The results will appear in the main <strong>"AI Analysis & Chat Interface"</strong> window. Findings are marked with colored dots for easy identification:
            </p>
            <ul>
                <li><span style="color:#dc3545;">&#9679;</span> <strong>High Risk:</strong> Critical issues that need immediate attention.</li>
                <li><span style="color:#f59e0b;">&#9679;</span> <strong>Medium Risk:</strong> Important issues to address.</li>
                <li><span style="color:#28a745;">&#9679;</span> <strong>Strengths:</strong> Areas where documentation is compliant and strong.</li>
            </ul>

            <h2 style="color: #4a90e2; border-bottom: 1px solid #4a4a4a; padding-bottom: 5px;">Step 5: Interact with the AI</h2>
            <p>
                Use the <strong>"AI Assistant"</strong> chat box at the bottom to ask for clarifications about the analysis, compliance rules, or documentation best practices. Simply type your question and press <strong>Enter</strong> to send.
            </p>
        </body>
        </html>
        """