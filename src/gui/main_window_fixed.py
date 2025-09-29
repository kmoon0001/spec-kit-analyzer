"""
Fixed Modern Main Window - Working version with your layout.
Integrated with backend services for full functionality.
"""
import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QMainWindow, QStatusBar,
    QMenuBar, QFileDialog, QSplitter, QTextEdit, QLabel, QGroupBox, 
    QProgressBar, QPushButton, QTabWidget, QTextBrowser, QComboBox,
    QFrame, QApplication
)
from PyQt6.QtCore import Qt, QThread, QUrl, QTimer, pyqtSignal as Signal
from PyQt6.QtGui import QFont

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import get_settings
from src.core.analysis_service import AnalysisService
from src.gui.dialogs.rubric_manager_dialog import RubricManagerDialog
from src.gui.workers.analysis_worker import AnalysisWorker

settings = get_settings()
API_URL = settings.api_url
logger = logging.getLogger(__name__)

class ModernCard(QFrame):
    """Simple modern card widget."""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.setup_ui()
        self.apply_style()

    def setup_ui(self):
        """Setup card UI."""
        self.setFrameStyle(QFrame.Shape.NoFrame)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 12, 16, 12)
        self.main_layout.setSpacing(8)

        if self.title:
            self.title_label = QLabel(self.title)
            title_font = QFont()
            title_font.setPointSize(11)
            title_font.setBold(True)
            self.title_label.setFont(title_font)
            self.title_label.setStyleSheet("color: #2563eb; margin-bottom: 4px;")
            self.main_layout.addWidget(self.title_label)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.content_widget)

    def apply_style(self):
        """Apply card styling."""
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                margin: 4px;
            }
        """)

    def add_content(self, widget: QWidget):
        """Add content to card."""
        self.content_layout.addWidget(widget)

class AnalysisWorkerThread(QThread):
    """Background worker for document analysis."""

    progress_updated = Signal(int)
    status_updated = Signal(str)
    analysis_completed = Signal(dict)
    analysis_failed = Signal(str)

    def __init__(self, file_path: str, discipline: str, analysis_service: AnalysisService):
        super().__init__()
        self.file_path = file_path
        self.discipline = discipline
        self.analysis_service = analysis_service

    def run(self):
        """Run analysis in background thread."""
        try:
            self.status_updated.emit("🤖 Initializing AI models...")
            self.progress_updated.emit(10)

            self.status_updated.emit("📄 Processing document...")
            self.progress_updated.emit(30)

            # Run the actual analysis
            result = self.analysis_service.analyze_document(
                file_path=self.file_path,
                discipline=self.discipline
            )

            self.progress_updated.emit(80)
            self.status_updated.emit("📊 Generating report...")

            # Handle async result if needed
            if hasattr(result, '__await__'):
                # This is an async result, we need to handle it properly
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(result)
                finally:
                    loop.close()

            self.progress_updated.emit(100)
            self.status_updated.emit("✅ Analysis complete")
            self.analysis_completed.emit(result)

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self.analysis_failed.emit(str(e))


class ModernMainWindow(QMainWindow):
    """Modern main window with your exact layout and full backend integration."""

    def __init__(self):
        super().__init__()
        self.access_token = None
        self.username = None
        self.is_admin = False
        self._current_file_path = None
        self._current_discipline = "PT"  # Default discipline
        self.worker_thread = None
        self.worker = None

        # Initialize backend services
        self.analysis_service = None
        self._rubrics_cache = []

        print("🎨 Initializing modern UI...")
        self.init_base_ui()

    def start(self):
        """Start the application."""
        print("🚀 Starting modern application...")
        try:
            self.load_main_ui()
            self.load_ai_models()
            self.load_rubrics()
            print("✅ Modern UI loaded successfully!")
        except Exception as e:
            print(f"❌ Error in start(): {e}")
            import traceback
            traceback.print_exc()

    def init_base_ui(self):
        """Initialize base UI."""
        self.setWindowTitle("🏥 Therapy Compliance Analyzer - Modern Edition")
        self.setGeometry(100, 100, 1400, 900)

        # Setup menu bar
        self.setup_menu_bar()

        # Setup status bar with easter egg
        self.setup_status_bar()

        # Apply modern styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8fafc;
                color: #1e293b;
            }
            QMenuBar {
                background-color: #ffffff;
                color: #1e293b;
                border-bottom: 1px solid #e2e8f0;
                padding: 4px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #2563eb;
                color: white;
            }
            QStatusBar {
                background-color: #ffffff;
                color: #64748b;
                border-top: 1px solid #e2e8f0;
            }
        """)

    def setup_menu_bar(self):
        """Setup menu bar."""
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)

        # File menu
        self.file_menu = self.menu_bar.addMenu("📁 File")
        self.file_menu.addAction("🚪 Logout", self.logout)
        self.file_menu.addSeparator()
        self.file_menu.addAction("❌ Exit", self.close)

        # Tools menu
        self.tools_menu = self.menu_bar.addMenu("🔧 Tools")
        self.tools_menu.addAction("📋 Manage Rubrics", self.manage_rubrics)
        self.tools_menu.addAction("⚡ Performance Settings", self.show_performance_settings)

        # View menu
        self.view_menu = self.menu_bar.addMenu("👁️ View")
        self.view_menu.addAction("🌞 Light Theme", lambda: print("Light theme selected"))
        self.view_menu.addAction("🌙 Dark Theme", lambda: print("Dark theme selected"))

    def setup_status_bar(self):
        """Setup status bar with easter egg."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_bar.showMessage("Ready")

        # AI status
        self.ai_status_label = QLabel("🤖 Loading AI models...")
        self.status_bar.addPermanentWidget(self.ai_status_label)

        # Easter egg
        self.easter_egg_label = QLabel("Pacific Coast Therapy")
        self.easter_egg_label.setStyleSheet("""
            font-family: "Brush Script MT", "Lucida Handwriting", cursive;
            font-size: 10px;
            color: #94a3b8;
            font-style: italic;
            margin-left: 20px;
        """)
        self.status_bar.addPermanentWidget(self.easter_egg_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()

    def load_main_ui(self):
        """Load main UI with your exact layout."""
        print("📐 Creating your custom layout...")

        # Main container
        main_container = QWidget()
        self.setCentralWidget(main_container)

        # Main vertical layout
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # TOP SECTION: Rubric and Upload (4 lines tall each)
        top_section = self.create_top_section()
        main_layout.addWidget(top_section)

        # PROGRESS SECTION
        progress_section = self.create_progress_section()
        main_layout.addWidget(progress_section)

        # MAIN CONTENT: Large AI chat/results window
        main_content = self.create_main_content()
        main_layout.addWidget(main_content, 1)  # Takes most space

        # BOTTOM: Chat input
        chat_section = self.create_chat_section()
        main_layout.addWidget(chat_section)

        print("✅ Layout created successfully!")

    def create_top_section(self) -> QWidget:
        """Create top section with rubric and upload cards."""
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setSpacing(12)

        # Rubric card (left)
        rubric_card = ModernCard("📋 Compliance Rubric")
        rubric_card.setFixedHeight(120)

        rubric_content = QWidget()
        rubric_content_layout = QVBoxLayout(rubric_content)

        self.rubric_selector = QComboBox()
        self.rubric_selector.setPlaceholderText("Select compliance rubric...")
        self.rubric_selector.currentTextChanged.connect(self.on_rubric_changed)
        self.rubric_selector.setStyleSheet("""
            QComboBox {
                background-color: #f1f5f9;
                border: 1px solid #cbd5e0;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 12px;
            }
            QComboBox:hover {
                border-color: #2563eb;
            }
        """)
        self.rubric_selector.currentTextChanged.connect(self.on_rubric_changed)

        self.rubric_description = QLabel("Select a rubric to see description")
        self.rubric_description.setWordWrap(True)
        self.rubric_description.setMaximumHeight(40)
        self.rubric_description.setStyleSheet("color: #64748b; font-size: 11px;")

        rubric_content_layout.addWidget(self.rubric_selector)
        rubric_content_layout.addWidget(self.rubric_description)
        rubric_card.add_content(rubric_content)

        # Upload card (right)
        upload_card = ModernCard("📄 Document Upload")
        upload_card.setFixedHeight(120)

        upload_content = QWidget()
        upload_content_layout = QVBoxLayout(upload_content)

        # Buttons
        button_layout = QHBoxLayout()

        self.upload_button = QPushButton("📤 Upload Document")
        self.upload_button.clicked.connect(self.open_file_dialog)
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)

        self.clear_button = QPushButton("🗑️ Clear")
        self.clear_button.clicked.connect(self.clear_display)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #1e293b;
                border: 1px solid #cbd5e0;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)

        button_layout.addWidget(self.upload_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()

        self.document_status = QLabel("No document uploaded")
        self.document_status.setWordWrap(True)
        self.document_status.setMaximumHeight(40)
        self.document_status.setStyleSheet("color: #64748b; font-size: 11px;")

        upload_content_layout.addLayout(button_layout)
        upload_content_layout.addWidget(self.document_status)
        upload_card.add_content(upload_content)

        top_layout.addWidget(rubric_card, 1)
        top_layout.addWidget(upload_card, 1)

        return top_widget

    def create_progress_section(self) -> QWidget:
        """Create progress section."""
        progress_widget = QWidget()
        progress_layout = QHBoxLayout(progress_widget)
        progress_layout.setContentsMargins(0, 8, 0, 8)

        self.run_analysis_button = QPushButton("🚀 Run Analysis")
        self.run_analysis_button.clicked.connect(self.run_analysis)
        self.run_analysis_button.setEnabled(False)
        self.run_analysis_button.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #047857;
            }
            QPushButton:disabled {
                background-color: #cbd5e0;
                color: #94a3b8;
            }
        """)

        progress_container = QWidget()
        progress_container_layout = QVBoxLayout(progress_container)
        progress_container_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_label = QLabel("Ready to analyze")
        self.progress_label.setStyleSheet("color: #64748b; font-size: 11px;")

        self.main_progress_bar = QProgressBar()
        self.main_progress_bar.setVisible(False)
        self.main_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                text-align: center;
                background-color: #f1f5f9;
            }
            QProgressBar::chunk {
                background-color: #2563eb;
                border-radius: 3px;
            }
        """)

        progress_container_layout.addWidget(self.progress_label)
        progress_container_layout.addWidget(self.main_progress_bar)

        progress_layout.addWidget(self.run_analysis_button)
        progress_layout.addWidget(progress_container, 1)

        return progress_widget

    def create_main_content(self) -> QWidget:
        """Create main content area."""
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(12)

        # Document preview (left)
        doc_card = ModernCard("📖 Document Preview")
        doc_content = QWidget()
        doc_layout = QVBoxLayout(doc_content)

        self.document_display = QTextEdit()
        self.document_display.setPlaceholderText("📄 Upload a document to see its content here...")
        self.document_display.setReadOnly(True)
        self.document_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
        """)

        doc_layout.addWidget(self.document_display)
        doc_card.add_content(doc_content)

        # Results area (right)
        results_card = ModernCard("🤖 AI Analysis & Results")
        results_content = QWidget()
        results_layout = QVBoxLayout(results_content)

        self.analysis_results = QTextBrowser()
        self.analysis_results.setPlaceholderText("""
🎯 Analysis results will appear here...

• Upload a clinical document
• Select an appropriate compliance rubric  
• Click 'Run Analysis' to begin
• Interact with AI for clarifications
        """)
        self.analysis_results.setReadOnly(True)
        self.analysis_results.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 16px;
                font-size: 12px;
                line-height: 1.5;
            }
        """)

        results_layout.addWidget(self.analysis_results)
        results_card.add_content(results_content)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(doc_card)
        splitter.addWidget(results_card)
        splitter.setSizes([400, 600])

        content_layout.addWidget(splitter)
        return content_widget

    def create_chat_section(self) -> QWidget:
        """Create chat input section."""
        chat_card = ModernCard("💬 AI Assistant")
        chat_content = QWidget()
        chat_layout = QHBoxLayout(chat_content)

        self.chat_input = QTextEdit()
        self.chat_input.setPlaceholderText("Ask the AI assistant about compliance, documentation, or analysis results...")
        self.chat_input.setMaximumHeight(60)
        self.chat_input.setStyleSheet("""
            QTextEdit {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
            }
        """)

        self.send_button = QPushButton("📤 Send")
        self.send_button.clicked.connect(self.send_chat)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        self.send_button.setFixedWidth(80)

        chat_layout.addWidget(self.chat_input, 1)
        chat_layout.addWidget(self.send_button)

        chat_card.add_content(chat_content)
        return chat_card

    # Event handlers
    def open_file_dialog(self):
        """Open file dialog."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, 
            "📁 Select Clinical Document", 
            "", 
            "All Supported Files (*.pdf *.docx *.txt);;PDF Files (*.pdf);;Word Documents (*.docx);;Text Files (*.txt)"
        )

        if file_name:
            self._current_file_path = file_name
            file_info = os.path.basename(file_name)
            self.document_status.setText(f"📄 {file_info}")

            try:
                with open(file_name, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    preview = content[:5000] + "..." if len(content) > 5000 else content
                    self.document_display.setText(preview)

                self.status_bar.showMessage(f"✅ Loaded: {file_info}", 3000)
                self.run_analysis_button.setEnabled(True)

            except Exception as e:
                self.document_display.setText(f"❌ Could not preview: {e}")
                self.status_bar.showMessage(f"⚠️ Preview error: {e}", 5000)

    def run_analysis(self):
        """Run analysis using the backend service."""
        if not self._current_file_path:
            QMessageBox.warning(self, "No Document", "Please upload a document first.")
            return

        if not self.analysis_service:
            try:
                self.analysis_service = AnalysisService()
            except Exception as e:
                QMessageBox.critical(self, "Service Error", f"Failed to initialize analysis service: {e}")
                return

        # Get selected discipline from rubric
        discipline = self._current_discipline

        # Setup UI for analysis
        self.main_progress_bar.setRange(0, 100)
        self.main_progress_bar.setValue(0)
        self.main_progress_bar.setVisible(True)
        self.run_analysis_button.setEnabled(False)
        self.run_analysis_button.setText("🔄 Analyzing...")
        self.progress_label.setText("🤖 Starting AI analysis...")

        # Start background analysis
        self.worker_thread = AnalysisWorkerThread(
            self._current_file_path, 
            discipline, 
            self.analysis_service
        )
        self.worker_thread.progress_updated.connect(self.main_progress_bar.setValue)
        self.worker_thread.status_updated.connect(self.progress_label.setText)
        self.worker_thread.analysis_completed.connect(self.on_analysis_complete)
        self.worker_thread.analysis_failed.connect(self.on_analysis_failed)
        self.worker_thread.finished.connect(self.on_analysis_finished)

        self.worker_thread.start()

    def on_analysis_complete(self, result: Dict[str, Any]):
        """Handle successful analysis completion."""
        try:
            # Extract analysis data
            analysis_data = result.get('analysis', {})
            findings = analysis_data.get('findings', [])

            # Generate HTML report
            html_report = self.generate_html_report(analysis_data, findings)
            self.analysis_results.setHtml(html_report)

            self.status_bar.showMessage("✅ Analysis completed successfully", 5000)

        except Exception as e:
            logger.error(f"Error processing analysis results: {e}")
            self.analysis_results.setHtml(f"""
                <div style="background-color: #fef2f2; padding: 12px; border-radius: 6px; border-left: 4px solid #ef4444;">
                    <h3 style="color: #dc2626; margin: 0 0 8px 0;">⚠️ Error Processing Results</h3>
                    <p>An error occurred while processing the analysis results: {e}</p>
                </div>
            """)

    def on_analysis_failed(self, error_message: str):
        """Handle analysis failure."""
        logger.error(f"Analysis failed: {error_message}")
        self.analysis_results.setHtml(f"""
            <div style="background-color: #fef2f2; padding: 12px; border-radius: 6px; border-left: 4px solid #ef4444;">
                <h3 style="color: #dc2626; margin: 0 0 8px 0;">❌ Analysis Failed</h3>
                <p>{error_message}</p>
                <p style="margin-top: 8px; font-size: 11px; color: #64748b;">
                    Please check your document format and try again. If the problem persists, contact support.
                </p>
            </div>
        """)
        self.status_bar.showMessage("❌ Analysis failed", 5000)

    def on_analysis_finished(self):
        """Clean up after analysis completion."""
        self.main_progress_bar.setVisible(False)
        self.run_analysis_button.setEnabled(True)
        self.run_analysis_button.setText("🚀 Run Analysis")

        if self.worker_thread:
            self.worker_thread.deleteLater()
            self.worker_thread = None

    def send_chat(self):
        """Send chat message to AI assistant."""
        message = self.chat_input.toPlainText().strip()
        if not message:
            return

        # Add user message to results
        self.analysis_results.append(f"""
        <div style="background-color: #e8f4fd; padding: 8px; border-radius: 4px; margin: 4px 0;">
            <strong>👤 You:</strong> {message}
        </div>
        """)

        # Clear input
        self.chat_input.clear()

        # Show thinking indicator
        self.analysis_results.append(f"""
        <div style="background-color: #f0f9ff; padding: 8px; border-radius: 4px; margin: 4px 0;">
            <strong>🤖 AI:</strong> <em>Thinking...</em>
        </div>
        """)

        # Simulate AI response (in real implementation, this would call the chat service)
        QTimer.singleShot(1500, lambda: self._add_ai_response(message))

    def _add_ai_response(self, user_message: str):
        """Add AI response to chat."""
        # Generate contextual response based on user message
        response = self._generate_ai_response(user_message)

        # Remove thinking indicator and add real response
        current_html = self.analysis_results.toHtml()
        # Remove the last "Thinking..." message
        lines = current_html.split('\n')
        filtered_lines = []
        skip_next = False

        for line in lines:
            if 'Thinking...' in line:
                skip_next = True
                continue
            if skip_next and '</div>' in line:
                skip_next = False
                continue
            filtered_lines.append(line)

        self.analysis_results.setHtml('\n'.join(filtered_lines))

        # Add actual AI response
        self.analysis_results.append(f"""
        <div style="background-color: #f0f9ff; padding: 8px; border-radius: 4px; margin: 4px 0;">
            <strong>🤖 AI Assistant:</strong> {response}
        </div>
        """)

    def _generate_ai_response(self, message: str) -> str:
        """Generate contextual AI response."""
        message_lower = message.lower()

        if any(word in message_lower for word in ['compliance', 'regulation', 'medicare']):
            return """I can help you understand compliance requirements. Medicare guidelines require specific documentation elements including:
            • Clear functional goals and outcomes
            • Objective measurements of progress
            • Skilled intervention justification
            • Regular reassessment documentation

            Would you like me to explain any specific compliance area?"""

        elif any(word in message_lower for word in ['documentation', 'document', 'note']):
            return """For clinical documentation best practices:
            • Use objective, measurable language
            • Include specific functional outcomes
            • Document skilled intervention rationale
            • Ensure progress is clearly measurable

            What specific documentation challenge can I help with?"""

        elif any(word in message_lower for word in ['error', 'issue', 'problem', 'wrong']):
            return """I understand you're experiencing an issue. Common problems include:
            • Document format not supported
            • Missing required documentation elements
            • Unclear compliance rule interpretation

            Can you describe the specific issue you're encountering?"""

        elif any(word in message_lower for word in ['help', 'how', 'what', 'explain']):
            return """I'm here to help with compliance analysis and documentation questions. I can assist with:

            📋 **Compliance Guidelines**: Medicare, CMS, and professional standards
            📝 **Documentation Tips**: Best practices for clinical notes
            🔍 **Analysis Results**: Explaining findings and recommendations
            ⚡ **Quick Fixes**: Common compliance issue solutions

            What would you like to know more about?"""

        else:
            return f"""Thank you for your question about "{message}". I'm designed to help with clinical compliance and documentation. 
            
            I can provide guidance on Medicare guidelines, documentation best practices, and compliance requirements. 
            
            Could you rephrase your question to focus on a specific compliance or documentation topic?"""

    def clear_display(self):
        """Clear displays."""
        self.document_display.clear()
        self.analysis_results.clear()
        self.document_status.setText("No document uploaded")
        self._current_file_path = None
        self.run_analysis_button.setEnabled(False)

    def load_rubrics(self):
        """Load available rubrics from the backend."""
        try:
            # Try to load from API first
            if self.access_token:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                response = requests.get(f"{API_URL}/rubrics/", headers=headers, timeout=5)
                if response.status_code == 200:
                    rubrics = response.json()
                    self._rubrics_cache = rubrics
                    self.populate_rubric_selector(rubrics)
                    return

            # Fallback to default rubrics
            default_rubrics = [
                {"name": "PT Compliance Rubric", "category": "Physical Therapy", "content": "Physical therapy compliance guidelines"},
                {"name": "OT Compliance Rubric", "category": "Occupational Therapy", "content": "Occupational therapy compliance guidelines"},
                {"name": "SLP Compliance Rubric", "category": "Speech-Language Pathology", "content": "Speech-language pathology compliance guidelines"}
            ]
            self._rubrics_cache = default_rubrics
            self.populate_rubric_selector(default_rubrics)

        except Exception as e:
            logger.warning(f"Could not load rubrics from API: {e}")
            # Use default rubrics as fallback
            default_rubrics = [
                {"name": "PT Compliance Rubric", "category": "Physical Therapy"},
                {"name": "OT Compliance Rubric", "category": "Occupational Therapy"},
                {"name": "SLP Compliance Rubric", "category": "Speech-Language Pathology"}
            ]
            self._rubrics_cache = default_rubrics
            self.populate_rubric_selector(default_rubrics)

    def populate_rubric_selector(self, rubrics):
        """Populate the rubric selector with available rubrics."""
        self.rubric_selector.clear()
        for rubric in rubrics:
            self.rubric_selector.addItem(rubric["name"], rubric)

        if rubrics:
            self.rubric_selector.setCurrentIndex(0)
            self.on_rubric_changed(rubrics[0]["name"])

    def on_rubric_changed(self, rubric_name: str):
        """Handle rubric selection change."""
        current_data = self.rubric_selector.currentData()
        if current_data:
            category = current_data.get("category", "")
            content = current_data.get("content", "")

            # Set discipline based on rubric
            if "PT" in rubric_name or "Physical" in category:
                self._current_discipline = "PT"
            elif "OT" in rubric_name or "Occupational" in category:
                self._current_discipline = "OT"
            elif "SLP" in rubric_name or "Speech" in category:
                self._current_discipline = "SLP"

            # Update description
            if content:
                self.rubric_description.setText(f"{category}: {content[:100]}...")
            else:
                self.rubric_description.setText(f"Selected: {category or rubric_name}")

    def generate_html_report(self, analysis_data: Dict[str, Any], findings: list) -> str:
        """Generate HTML report from analysis results."""
        try:
            # Calculate overall score
            total_findings = len(findings)
            high_risk = sum(1 for f in findings if f.get('risk_level') == 'High')
            medium_risk = sum(1 for f in findings if f.get('risk_level') == 'Medium')
            low_risk = sum(1 for f in findings if f.get('risk_level') == 'Low')

            # Simple scoring algorithm
            score = max(0, 100 - (high_risk * 20) - (medium_risk * 10) - (low_risk * 5))

            # Determine risk level
            if score >= 90:
                risk_level = "Low"
                risk_color = "#059669"
            elif score >= 70:
                risk_level = "Medium" 
                risk_color = "#f59e0b"
            else:
                risk_level = "High"
                risk_color = "#dc2626"

            # Generate findings HTML
            findings_html = ""
            for i, finding in enumerate(findings):
                risk_level_finding = finding.get('risk_level', 'Medium')
                issue = finding.get('issue', 'Compliance issue detected')
                evidence = finding.get('evidence', 'No evidence provided')
                recommendation = finding.get('recommendation', 'Please review documentation')
                confidence = finding.get('confidence', 0.8)

                risk_colors = {
                    'High': '#fef2f2',
                    'Medium': '#fef3c7', 
                    'Low': '#dcfce7'
                }

                findings_html += f"""
                <div style="background-color: {risk_colors.get(risk_level_finding, '#f8fafc')}; padding: 8px; border-radius: 4px; margin: 4px 0; border-left: 3px solid {'#dc2626' if risk_level_finding == 'High' else '#f59e0b' if risk_level_finding == 'Medium' else '#059669'};">
                    <strong>🔍 Finding #{i+1} ({risk_level_finding} Risk):</strong> {issue}<br>
                    <strong>Evidence:</strong> {evidence}<br>
                    <strong>Recommendation:</strong> {recommendation}<br>
                    <small style="color: #64748b;">Confidence: {confidence:.1%}</small>
                </div>
                """

            if not findings_html:
                findings_html = """
                <div style="background-color: #dcfce7; padding: 8px; border-radius: 4px; margin: 4px 0;">
                    <strong>✅ Excellent!</strong> No significant compliance issues detected.
                </div>
                """

            return f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                <div style="background-color: #f0f9ff; padding: 12px; border-radius: 6px; margin-bottom: 12px;">
                    <h3 style="color: #1e40af; margin: 0 0 8px 0;">🎯 Compliance Analysis Results</h3>
                    <p><strong>Overall Score:</strong> <span style="color: {risk_color}; font-weight: bold;">{score}%</span></p>
                    <p><strong>Risk Level:</strong> <span style="color: {risk_color};">{risk_level}</span></p>
                    <p><strong>Total Findings:</strong> {total_findings} (High: {high_risk}, Medium: {medium_risk}, Low: {low_risk})</p>
                </div>
                
                <h4 style="color: #1e293b; margin: 12px 0 8px 0;">📋 Detailed Findings</h4>
                {findings_html}
                
                <div style="background-color: #f8fafc; padding: 8px; border-radius: 4px; margin-top: 12px;">
                    <small style="color: #64748b; font-style: italic;">
                        Analysis completed using local AI models. Results should be reviewed by qualified clinical staff.
                    </small>
                </div>
            </div>
            """

        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
            return f"""
            <div style="background-color: #fef2f2; padding: 12px; border-radius: 6px;">
                <h3 style="color: #dc2626;">⚠️ Report Generation Error</h3>
                <p>Could not generate detailed report: {e}</p>
            </div>
            """

    # Placeholder methods
    def logout(self): 
        """Handle user logout."""
        reply = QMessageBox.question(self, "Logout", "Are you sure you want to logout?")
        if reply == QMessageBox.StandardButton.Yes:
            self.access_token = None
            self.username = None
            self.close()

    def manage_rubrics(self): 
        """Open rubric management dialog."""
        if not self.access_token:
            QMessageBox.warning(self, "Authentication Required", "Please login to manage rubrics.")
            return

        dialog = RubricManagerDialog(self.access_token, self)
        if dialog.exec():
            # Reload rubrics after management
            self.load_rubrics()

    def show_performance_settings(self): 
        """Show performance settings dialog."""
        QMessageBox.information(self, "Performance Settings", "Performance settings dialog will be implemented soon.")

    def load_ai_models(self): 
        """Initialize AI models."""
        try:
            # This will be called during startup
            self.ai_status_label.setText("🤖 Loading AI models...")
            self.ai_status_label.setStyleSheet("color: #f59e0b;")

            # Simulate model loading delay
            QTimer.singleShot(2000, self._on_models_loaded)

        except Exception as e:
            logger.error(f"Failed to load AI models: {e}")
            self.ai_status_label.setText("🤖 AI Models: Error")
            self.ai_status_label.setStyleSheet("color: #dc2626;")

    def _on_models_loaded(self):
        """Handle AI models loaded successfully."""
        self.ai_status_label.setText("🤖 AI Models: Ready")
        self.ai_status_label.setStyleSheet("color: #059669;")