"""
Modern Main Window - Redesigned with medical theme and your exact layout specifications.
"""
import os
import requests
import urllib.parse
import webbrowser
import jwt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QMainWindow, QStatusBar,
    QMenuBar, QFileDialog, QSplitter, QTextEdit, QLabel, QGroupBox, 
    QProgressBar, QPushButton, QTabWidget, QTextBrowser, QComboBox,
    QListWidget, QListWidgetItem, QFrame, QScrollArea, QGridLayout,
    QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QThread, QUrl, QTimer, pyqtSignal
from PyQt6.QtGui import QTextDocument, QFont, QIcon, QPixmap

# Import our new modern components
from .widgets.modern_card import ModernCard, ComplianceCard
from .widgets.medical_theme import medical_theme
from .widgets.quadrant_widget import QuadrantWidget
from .widgets.responsive_layout import ResponsiveWidget, VirtualScrollArea
from .widgets.micro_interactions import AnimatedButton, FadeInWidget, LoadingSpinner

# Import existing components
from .dialogs.rubric_manager_dialog import RubricManagerDialog
from .dialogs.change_password_dialog import ChangePasswordDialog
from .dialogs.chat_dialog import ChatDialog
from .dialogs.performance_settings_dialog import PerformanceSettingsDialog
from .dialogs.synergy_session_dialog import SynergySessionDialog
from .dialogs.review_dashboard_dialog import ReviewDashboardDialog
from .workers.analysis_starter_worker import AnalysisStarterWorker
from .workers.analysis_worker import AnalysisWorker
from .workers.ai_loader_worker import AILoaderWorker
from .workers.dashboard_worker import DashboardWorker
from .workers.review_worker import ReviewRequestWorker
from .widgets.dashboard_widget import DashboardWidget
from .widgets.performance_status_widget import PerformanceStatusWidget
from ..config import get_settings

settings = get_settings()
API_URL = settings.api_url

class ModernMainWindow(QMainWindow):
    """Modern, medical-themed main window with your exact layout specifications."""

    def __init__(self):
        super().__init__()
        self.access_token = None
        self.username = None
        self.user_role = "therapist" # Default role
        self.is_admin = False
        self._current_file_path = None
        self._current_folder_path = None
        self._current_report_id = None  # To store the ID of the latest report
        self.compliance_service = None
        self.worker_thread = None
        self.worker = None

        # Theme management
        self.current_theme = 'light'

        # Initialize UI
        self.init_base_ui()
        self.setup_medical_theme()

    def set_user_session(self, access_token: str):
        """Sets the user's session token and decodes it to get role information."""
        self.access_token = access_token
        try:
            # Decode the token without verification to inspect its contents
            decoded_token = jwt.decode(access_token, options={"verify_signature": False})
            self.user_role = decoded_token.get("role", "therapist")
            self.username = decoded_token.get("sub", "Unknown User")
        except jwt.PyJWTError:
            self.user_role = "therapist" # Default on error
            self.username = "Unknown User"

        # Update UI based on role
        self.setup_menu_bar()


    def start(self):
        """Start the application with modern loading experience."""
        self.load_ai_models()
        self.load_main_ui()
        self.show()

    def init_base_ui(self):
        """Initialize base UI with modern medical styling."""
        self.setWindowTitle("Therapy Compliance Analyzer")
        self.setGeometry(100, 100, 1400, 900)  # Larger default size

        # Setup menu bar
        self.setup_menu_bar()

        # Setup status bar with easter egg
        self.setup_status_bar()

        # Apply initial theme
        self.apply_medical_theme()

    def setup_menu_bar(self):
        """Setup modern menu bar, now role-aware."""
        if hasattr(self, 'menu_bar') and self.menu_bar:
            self.menu_bar.clear()
        else:
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
        self.tools_menu.addAction("🤝 Synergy Session", self.show_synergy_session)

        # Role-specific menu item for supervisors
        if self.user_role == "supervisor":
            self.tools_menu.addSeparator()
            self.tools_menu.addAction("👀 Review Dashboard", self.show_review_dashboard)

        self.tools_menu.addSeparator()
        self.tools_menu.addAction("⚡ Performance Settings", self.show_performance_settings)
        self.tools_menu.addAction("🔑 Change Password", self.show_change_password_dialog)

        # View menu
        self.view_menu = self.menu_bar.addMenu("👁️ View")
        self.view_menu.addAction("🌞 Light Theme", lambda: self.set_theme('light'))
        self.view_menu.addAction("🌙 Dark Theme", lambda: self.set_theme('dark'))
        self.view_menu.addSeparator()
        self.view_menu.addAction("📊 Compliance Guide", self.show_compliance_guide)

    def setup_status_bar(self):
        """Setup status bar with easter egg."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Main status message
        self.status_bar.showMessage("Ready")

        # AI status indicator
        self.ai_status_label = QLabel("🤖 Loading AI models...")
        self.status_bar.addPermanentWidget(self.ai_status_label)

        # Performance status widget
        self.performance_status = PerformanceStatusWidget()
        self.performance_status.settings_requested.connect(self.show_performance_settings)
        self.status_bar.addPermanentWidget(self.performance_status)

        # Easter egg - Pacific Coast Therapy in cursive
        self.easter_egg_label = QLabel("Pacific Coast Therapy")
        self.easter_egg_label.setObjectName("easter_egg")
        self.easter_egg_label.setStyleSheet("""
            font-family: "Brush Script MT", "Lucida Handwriting", cursive;
            font-size: 10px;
            color: #94a3b8;
            font-style: italic;
            margin-left: 20px;
        """)
        self.status_bar.addPermanentWidget(self.easter_egg_label)

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar(self.status_bar)
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()

    def setup_medical_theme(self):
        """Setup medical theme system."""
        medical_theme.theme_changed.connect(self.on_theme_changed)

    def apply_medical_theme(self):
        """Apply the current medical theme."""
        # Apply main window stylesheet
        self.setStyleSheet(medical_theme.get_main_window_stylesheet())

    def set_theme(self, theme: str):
        """Set the application theme."""
        self.current_theme = theme
        medical_theme.set_theme(theme)
        self.apply_medical_theme()

    def on_theme_changed(self, theme: str):
        """Handle theme change."""
        self.current_theme = theme
        self.apply_medical_theme()

    def load_main_ui(self):
        """Load the main UI with your exact layout specifications."""
        # Create main container
        main_container = ResponsiveWidget()
        self.setCentralWidget(main_container)

        # Main vertical layout
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # TOP SECTION: Rubric and Upload Windows (4 lines tall each)
        top_section = self.create_top_section()
        main_layout.addWidget(top_section)

        # PROGRESS BAR SECTION
        self.progress_section = self.create_progress_section()
        main_layout.addWidget(self.progress_section)

        # Language Score Section
        self.language_score_section = self.create_language_score_section()
        main_layout.addWidget(self.language_score_section)

        # MAIN CONTENT: AI Chat/Results Window (largest)
        main_content = self.create_main_content_section()
        main_layout.addWidget(main_content, 1)  # Stretch factor 1

        # BOTTOM: Chat Input Box
        chat_input_section = self.create_chat_input_section()
        main_layout.addWidget(chat_input_section)

        # Setup responsive behavior
        main_container.breakpoint_changed.connect(self.adapt_layout)

        # Load initial data
        self.load_dashboard_data()

    def create_top_section(self) -> QWidget:
        """Create top section with rubric and upload windows."""
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setSpacing(12)

        # Rubric Selection Card (left side)
        rubric_card = ModernCard("📋 Compliance Rubric")
        rubric_card.setFixedHeight(120)  # 4 lines tall

        rubric_content = QWidget()
        rubric_layout = QVBoxLayout(rubric_content)

        # Rubric selector
        self.rubric_selector = QComboBox()
        self.rubric_selector.setPlaceholderText("Select compliance rubric...")
        self.rubric_selector.currentIndexChanged.connect(self._on_rubric_selected)
        self.rubric_selector.setStyleSheet(medical_theme.get_button_stylesheet('secondary'))

        # Rubric description (2 lines)
        self.rubric_description_label = QLabel("Select a rubric to see description")
        self.rubric_description_label.setWordWrap(True)
        self.rubric_description_label.setMaximumHeight(40)  # 2 lines
        self.rubric_description_label.setStyleSheet("color: #64748b; font-size: 11px;")

        rubric_layout.addWidget(self.rubric_selector)
        rubric_layout.addWidget(self.rubric_description_label)
        rubric_card.add_content(rubric_content)

        # Document Upload Card (right side)
        upload_card = ModernCard("📄 Document Upload")
        upload_card.setFixedHeight(120)  # 4 lines tall

        upload_content = QWidget()
        upload_layout = QVBoxLayout(upload_content)

        # Upload button row
        upload_button_layout = QHBoxLayout()

        self.upload_button = AnimatedButton("📤 Upload Document")
        self.upload_button.clicked.connect(self.open_file_dialog)
        self.upload_button.setStyleSheet(medical_theme.get_button_stylesheet('primary'))

        self.clear_button = AnimatedButton("🗑️ Clear")
        self.clear_button.clicked.connect(self.clear_display)
        self.clear_button.setStyleSheet(medical_theme.get_button_stylesheet('secondary'))

        upload_button_layout.addWidget(self.upload_button)
        upload_button_layout.addWidget(self.clear_button)
        upload_button_layout.addStretch()

        # Document status (2 lines)
        self.document_status_label = QLabel("No document uploaded")
        self.document_status_label.setWordWrap(True)
        self.document_status_label.setMaximumHeight(40)  # 2 lines
        self.document_status_label.setStyleSheet("color: #64748b; font-size: 11px;")

        upload_layout.addLayout(upload_button_layout)
        upload_layout.addWidget(self.document_status_label)
        upload_card.add_content(upload_content)

        # Add cards to layout
        top_layout.addWidget(rubric_card, 1)
        top_layout.addWidget(upload_card, 1)

        return top_widget

    def create_progress_section(self) -> QWidget:
        """Create progress bar section."""
        progress_widget = FadeInWidget()
        progress_layout = QHBoxLayout(progress_widget)
        progress_layout.setContentsMargins(0, 8, 0, 8)

        # Analysis button
        self.run_analysis_button = AnimatedButton("🚀 Run Analysis")
        self.run_analysis_button.clicked.connect(self.run_analysis)
        self.run_analysis_button.setEnabled(False)
        self.run_analysis_button.setStyleSheet(medical_theme.get_button_stylesheet('success'))

        # Progress bar with label
        progress_container = QWidget()
        progress_container_layout = QVBoxLayout(progress_container)
        progress_container_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_label = QLabel("Ready to analyze")
        self.progress_label.setStyleSheet("color: #64748b; font-size: 11px;")

        self.main_progress_bar = QProgressBar()
        self.main_progress_bar.setVisible(False)
        self.main_progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {medical_theme.get_color('border_light')};
                border-radius: 4px;
                text-align: center;
                background-color: {medical_theme.get_color('bg_secondary')};
            }}
            QProgressBar::chunk {{
                background-color: {medical_theme.get_color('primary_blue')};
                border-radius: 3px;
            }}
        """)

        progress_container_layout.addWidget(self.progress_label)
        progress_container_layout.addWidget(self.main_progress_bar)

        # Loading spinner
        self.loading_spinner = LoadingSpinner(24)
        self.loading_spinner.setVisible(False)

        self.request_review_button = AnimatedButton("🧑‍🏫 Request Review")
        self.request_review_button.clicked.connect(self.request_review)
        self.request_review_button.setVisible(False)
        self.request_review_button.setStyleSheet(medical_theme.get_button_stylesheet('info'))

        progress_layout.addWidget(self.run_analysis_button)
        progress_layout.addWidget(self.request_review_button)
        progress_layout.addWidget(progress_container, 1)
        progress_layout.addWidget(self.loading_spinner)

        return progress_widget

    def create_main_content_section(self) -> QWidget:
        """Create main content section with AI chat and results."""
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(12)

        # Left side: Document preview
        document_card = ModernCard("📖 Document Preview")
        document_content = QWidget()
        document_layout = QVBoxLayout(document_content)

        self.document_display_area = QTextEdit()
        self.document_display_area.setPlaceholderText("📄 Upload a document to see its content here...")
        self.document_display_area.setReadOnly(True)
        self.document_display_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {medical_theme.get_color('bg_secondary')};
                border: 1px solid {medical_theme.get_color('border_light')};
                border-radius: 6px;
                padding: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                line-height: 1.4;
            }}
        """)

        document_layout.addWidget(self.document_display_area)
        document_card.add_content(document_content)

        # Right side: Analysis results and AI chat
        results_card = ModernCard("🤖 AI Analysis & Chat")
        results_content = QWidget()
        results_layout = QVBoxLayout(results_content)

        # Results area is now the QuadrantWidget
        self.analysis_results_area = QuadrantWidget()
        results_layout.addWidget(self.analysis_results_area)
        results_card.add_content(results_content)

        # Add to main layout with responsive splitter
        from .widgets.responsive_layout import ResponsiveSplitter
        splitter = ResponsiveSplitter()
        splitter.addWidget(document_card)
        splitter.addWidget(results_card)
        splitter.setSizes([400, 600])  # Results area larger

        content_layout.addWidget(splitter)

        return content_widget

    def create_chat_input_section(self) -> QWidget:
        """Create bottom chat input section."""
        chat_widget = ModernCard("💬 AI Assistant")
        chat_content = QWidget()
        chat_layout = QHBoxLayout(chat_content)

        # Chat input
        self.chat_input = QTextEdit()
        self.chat_input.setPlaceholderText("Ask the AI assistant about compliance, documentation, or analysis results...")
        self.chat_input.setMaximumHeight(60)
        self.chat_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {medical_theme.get_color('bg_secondary')};
                border: 1px solid {medical_theme.get_color('border_light')};
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
            }}
        """)

        # Send button
        self.send_chat_button = AnimatedButton("📤 Send")
        self.send_chat_button.clicked.connect(self.send_chat_message)
        self.send_chat_button.setStyleSheet(medical_theme.get_button_stylesheet('primary'))
        self.send_chat_button.setFixedWidth(80)

        # Voice input button (future feature)
        self.voice_button = AnimatedButton("🎤")
        self.voice_button.setToolTip("Voice input (coming soon)")
        self.voice_button.setEnabled(False)
        self.voice_button.setFixedWidth(40)
        self.voice_button.setStyleSheet(medical_theme.get_button_stylesheet('secondary'))

        chat_layout.addWidget(self.chat_input, 1)
        chat_layout.addWidget(self.voice_button)
        chat_layout.addWidget(self.send_chat_button)

        chat_widget.add_content(chat_content)
        return chat_widget

    def adapt_layout(self, breakpoint: str):
        """Adapt layout based on screen size."""
        if breakpoint == 'mobile':
            # Stack elements vertically on mobile
            pass
        elif breakpoint == 'tablet':
            # Adjust spacing and sizes for tablet
            pass
        # Desktop and large screens use default layout

    def create_language_score_section(self) -> QWidget:
        """Create the dedicated card for the patient-centered language score."""
        self.language_card = ModernCard("🗣️ Patient-Centered Language")

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        # Score display
        score_layout = QHBoxLayout()
        score_label = QLabel("Score:")
        self.language_score_value = QLabel("N/A")
        self.language_score_value.setStyleSheet("font-size: 18px; font-weight: bold;")
        score_layout.addWidget(score_label)
        score_layout.addWidget(self.language_score_value)
        score_layout.addStretch()

        # Recommendation
        self.language_recommendation = QLabel("Analysis pending...")
        self.language_recommendation.setWordWrap(True)

        layout.addLayout(score_layout)
        layout.addWidget(self.language_recommendation)

        self.language_card.add_content(content_widget)
        self.language_card.setVisible(False) # Initially hidden
        return self.language_card

    # Event handlers and existing methods...
    def _on_rubric_selected(self, index):
        """Handle rubric selection."""
        selected_rubric = self.rubric_selector.itemData(index)
        if selected_rubric:
            self.rubric_description_label.setText(
                selected_rubric.get("description", "No description available.")
            )
            self.run_analysis_button.setEnabled(True)
            self.run_analysis_button.setText("🚀 Run Analysis")
        else:
            self.rubric_description_label.setText("Select a rubric to see description")
            self.run_analysis_button.setEnabled(False)

    def open_file_dialog(self):
        """Open file dialog with modern styling."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, 
            "📁 Select Clinical Document", 
            "", 
            "All Supported Files (*.pdf *.docx *.txt);;PDF Files (*.pdf);;Word Documents (*.docx);;Text Files (*.txt)"
        )

        if file_name:
            self._current_file_path = file_name

            # Update document status
            file_info = os.path.basename(file_name)
            self.document_status_label.setText(f"📄 {file_info}")

            # Load document content
            try:
                with open(file_name, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    self.document_display_area.setText(content[:5000] + "..." if len(content) > 5000 else content)

                self.status_bar.showMessage(f"✅ Loaded document: {file_info}", 3000)

            except Exception as e:
                self.document_display_area.setText(f"❌ Could not display preview: {e}")
                self.status_bar.showMessage(f"⚠️ Preview error: {e}", 5000)

    def run_analysis(self):
        """Run analysis with modern progress indication."""
        if not self._current_file_path:
            QMessageBox.warning(self, "No Document", "Please upload a document first.")
            return

        selected_rubric = self.rubric_selector.currentData()
        if not selected_rubric:
            QMessageBox.warning(self, "No Rubric", "Please select a compliance rubric.")
            return

        # Start analysis with visual feedback
        self.start_analysis_ui()

        # Performance optimization
        try:
            from ..core.performance_integration import optimize_for_analysis
            optimization_results = optimize_for_analysis()

            if optimization_results.get('recommendations'):
                recommendations = '\n'.join(optimization_results['recommendations'])
                self.progress_label.setText("⚡ Performance optimized")
        except Exception as e:
            print(f"Performance optimization failed: {e}")

        # Start analysis worker
        discipline = selected_rubric.get("discipline", "Unknown")
        rubric_id = selected_rubric.get("id")

        self.worker_thread = QThread()
        self.worker = AnalysisStarterWorker(
            self._current_file_path,
            {"discipline": discipline, "rubric_id": rubric_id},
            self.access_token,
        )
        self.worker.moveToThread(self.worker_thread)
        self.worker.success.connect(self.handle_analysis_started)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def start_analysis_ui(self):
        """Start analysis UI feedback."""
        self.main_progress_bar.setRange(0, 0)  # Indeterminate
        self.main_progress_bar.setVisible(True)
        self.loading_spinner.start_spinning()
        self.run_analysis_button.setEnabled(False)
        self.run_analysis_button.setText("🔄 Analyzing...")
        self.progress_label.setText("🤖 AI analysis in progress...")

    def send_chat_message(self):
        """Opens a new chat dialog with the user's message as the initial context."""
        message = self.chat_input.toPlainText().strip()
        if not message:
            return

        if not self.access_token:
            QMessageBox.warning(self, "Authentication Error", "You must be logged in to use the chat feature.")
            return

        # Create and execute the chat dialog, which handles its own logic.
        try:
            chat_dialog = ChatDialog(initial_context=message, token=self.access_token, parent=self)
            chat_dialog.exec()  # .exec() makes the dialog modal.
        except Exception as e:
            QMessageBox.critical(self, "Chat Error", f"Could not open the chat window: {e}")
            logger.error(f"Failed to create or execute ChatDialog: {e}", exc_info=True)

        # Clear the input box in the main window after the chat is closed.
        self.chat_input.clear()

    # Placeholder methods for existing functionality
    def logout(self): pass
    def manage_rubrics(self): pass
    def show_performance_settings(self): pass
    def show_change_password_dialog(self): pass

    def show_synergy_session(self):
        """Shows the Synergy Session dialog for complex cases."""
        if not self.access_token:
            QMessageBox.warning(self, "Authentication Error", "You must be logged in to use this feature.")
            return

        try:
            dialog = SynergySessionDialog(token=self.access_token, parent=self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Dialog Error", f"Could not open the Synergy Session window: {e}")

    def show_review_dashboard(self):
        """Shows the Review Dashboard for supervisors."""
        if not self.access_token:
            QMessageBox.warning(self, "Authentication Error", "You must be logged in to use this feature.")
            return

        try:
            dialog = ReviewDashboardDialog(token=self.access_token, parent=self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Dialog Error", f"Could not open the Review Dashboard: {e}")

    def show_compliance_guide(self): pass

    def clear_display(self):
        """Clears the document view and analysis results."""
        self._current_file_path = None
        self._current_report_id = None
        self.document_display_area.clear()
        self.document_status_label.setText("No document uploaded")
        self.analysis_results_area.clear_findings()
        self.language_card.setVisible(False)
        self.request_review_button.setVisible(False)
        self.status_bar.showMessage("Display cleared.", 3000)

    def handle_anchor_click(self, url): pass

    def handle_analysis_started(self, task_id: str):
        """Handle successful start of analysis task."""
        self.progress_label.setText(f"✅ Task started (ID: {task_id[:8]}...). Polling for results.")

        # This worker will poll the API for the results
        self.polling_thread = QThread()
        self.polling_worker = AnalysisWorker(task_id, self.access_token)
        self.polling_worker.moveToThread(self.polling_thread)

        # Connect signals from the polling worker to the main thread
        self.polling_worker.success.connect(self.on_analysis_success)
        self.polling_worker.error.connect(self.on_analysis_error)
        self.polling_worker.progress.connect(self.update_progress)
        self.polling_worker.finished.connect(self.polling_thread.quit)
        self.polling_worker.finished.connect(self.polling_worker.deleteLater)
        self.polling_thread.finished.connect(self.polling_thread.deleteLater)

        self.polling_thread.started.connect(self.polling_worker.run)
        self.polling_thread.start()

    def on_analysis_success(self, result: dict):
        """Display the final analysis results and enable review functionality."""
        self.stop_analysis_ui(success=True)

        self._current_report_id = result.get("report_id")
        if self._current_report_id:
            self.request_review_button.setVisible(True)
            self.request_review_button.setEnabled(True)
            self.request_review_button.setText("🧑‍🏫 Request Review")
        else:
            self.request_review_button.setVisible(False)

        analysis_data = result.get('analysis', {})
        findings = analysis_data.get('findings', [])
        language_analysis = analysis_data.get('patient_centered_language_analysis', {})

        # 1. Populate Quadrant Widget
        self.analysis_results_area.display_findings(findings)

        # 2. Populate and show Language Score Card
        if language_analysis:
            score = language_analysis.get('score', 50)
            score_color = "#28a745" if score >= 75 else ("#ffc107" if score >= 50 else "#dc3545")
            self.language_score_value.setText(f"{score}%")
            self.language_score_value.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {score_color};")

            if score < 50:
                rec_text = "<b>Recommendation:</b> This documentation uses primarily passive or impersonal language..."
            elif score < 75:
                rec_text = "<b>Recommendation:</b> This is a good start. Increase patient-centered phrases..."
            else:
                rec_text = "<b>Excellent!</b> The language in this note is strongly patient-centered."
            self.language_recommendation.setText(rec_text)
            self.language_card.setVisible(True)
        else:
            self.language_card.setVisible(False)

    def on_analysis_error(self, error: str):
        """Handle analysis errors from any worker."""
        self.stop_analysis_ui(success=False)
        self._current_report_id = None
        self.analysis_results_area.clear_findings()
        self.language_card.setVisible(False)
        self.request_review_button.setVisible(False)
        QMessageBox.critical(self, "Analysis Error", f"An error occurred during analysis:\n\n{error}")

    def request_review(self):
        """Handles the 'Request Review' button click."""
        if not self._current_report_id:
            QMessageBox.warning(self, "No Report", "There is no report to request a review for.")
            return

        if not self.access_token:
            QMessageBox.warning(self, "Authentication Error", "You must be logged in to request a review.")
            return

        self.request_review_button.setEnabled(False)
        self.request_review_button.setText("Submitting...")

        self.review_worker_thread = QThread()
        self.review_worker = ReviewRequestWorker(self._current_report_id, self.access_token)
        self.review_worker.moveToThread(self.review_worker_thread)

        self.review_worker.success.connect(self.on_review_request_success)
        self.review_worker.error.connect(self.on_review_request_error)
        self.review_worker.finished.connect(self.review_worker_thread.quit)
        self.review_worker.finished.connect(self.review_worker.deleteLater)
        self.review_worker_thread.finished.connect(self.review_worker_thread.deleteLater)

        self.review_worker_thread.started.connect(self.review_worker.run)
        self.review_worker_thread.start()

    def on_review_request_success(self, message):
        """Handles a successful review request."""
        self.request_review_button.setText("Submitted!")
        QMessageBox.information(self, "Success", message)

    def on_review_request_error(self, error_message):
        """Handles an error during a review request."""
        self.request_review_button.setEnabled(True)
        self.request_review_button.setText("🧑‍🏫 Request Review")
        QMessageBox.critical(self, "Review Request Failed", error_message)

    def update_progress(self, value: int, message: str):
        """Update progress bar and label from worker."""
        self.progress_label.setText(f"🤖 {message}")
        if self.main_progress_bar.isIndeterminate():
            self.main_progress_bar.setRange(0,100)

        self.main_progress_bar.setValue(value)

    def stop_analysis_ui(self, success: bool = True):
        """Reset the UI after analysis is complete."""
        self.main_progress_bar.setVisible(False)
        self.main_progress_bar.setRange(0, 0) # Back to indeterminate
        self.loading_spinner.stop_spinning()
        self.run_analysis_button.setEnabled(True)
        self.run_analysis_button.setText("🚀 Run Analysis")
        self.progress_label.setText("✅ Analysis complete." if success else "❌ Analysis failed.")

    def load_ai_models(self): pass
    def load_dashboard_data(self): pass