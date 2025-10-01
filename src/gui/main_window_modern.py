"""
Modern Main Window - Redesigned with medical theme and your exact layout specifications.
"""

import os
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QStatusBar,
    QFileDialog,
    QTextEdit,
    QLabel,
    QProgressBar,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QMainWindow, QStatusBar,
    QMenuBar, QFileDialog, QTextEdit, QLabel, QProgressBar, QTextBrowser, QComboBox
)
from PyQt6.QtCore import QThread

# Import our new modern components
from src.gui.widgets.modern_card import ModernCard
from src.gui.widgets.medical_theme import medical_theme
from src.gui.widgets.responsive_layout import ResponsiveWidget
from src.gui.widgets.micro_interactions import AnimatedButton, FadeInWidget, LoadingSpinner
from src.gui.workers.analysis_starter_worker import AnalysisStarterWorker
from src.gui.widgets.performance_status_widget import PerformanceStatusWidget
from src.config import get_settings

settings = get_settings()
API_URL = settings.api_url


class ModernMainWindow(QMainWindow):
    """Modern, medical-themed main window with your exact layout specifications."""

    def __init__(self):
        super().__init__()
        self.access_token = None
        self.username = None
        self.is_admin = False
        self._current_file_path = None
        self._current_folder_path = None
        self.compliance_service = None
        self.worker_thread = None
        self.worker = None

        # Theme management
        self.current_theme = "light"

        # Initialize UI
        self.init_base_ui()
        self.setup_medical_theme()

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
        """Setup modern menu bar."""
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
        self.tools_menu.addAction(
            "⚡ Performance Settings", self.show_performance_settings
        )
        self.tools_menu.addAction(
            "🔑 Change Password", self.show_change_password_dialog
        )

        # View menu
        self.view_menu = self.menu_bar.addMenu("👁️ View")
        self.view_menu.addAction("🌞 Light Theme", lambda: self.set_theme("light"))
        self.view_menu.addAction("🌙 Dark Theme", lambda: self.set_theme("dark"))
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
        self.performance_status.settings_requested.connect(
            self.show_performance_settings
        )
        self.status_bar.addPermanentWidget(self.performance_status)

        # Easter egg - Pacific Coast Therapy in cursive
        self.easter_egg_label = QLabel("Pacific Coast Therapy")
        self.easter_egg_label.setObjectName("easter_egg")
        self.easter_egg_label.setStyleSheet(
            """
            font-family: "Brush Script MT", "Lucida Handwriting", cursive;
            font-size: 10px;
            color: #94a3b8;
            font-style: italic;
            margin-left: 20px;
        """
        )
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
        self.rubric_selector.setStyleSheet(
            medical_theme.get_button_stylesheet("secondary")
        )

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
        self.upload_button.setStyleSheet(medical_theme.get_button_stylesheet("primary"))

        self.clear_button = AnimatedButton("🗑️ Clear")
        self.clear_button.clicked.connect(self.clear_display)
        self.clear_button.setStyleSheet(
            medical_theme.get_button_stylesheet("secondary")
        )

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
        self.run_analysis_button.setStyleSheet(
            medical_theme.get_button_stylesheet("success")
        )

        # Progress bar with label
        progress_container = QWidget()
        progress_container_layout = QVBoxLayout(progress_container)
        progress_container_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_label = QLabel("Ready to analyze")
        self.progress_label.setStyleSheet("color: #64748b; font-size: 11px;")

        self.main_progress_bar = QProgressBar()
        self.main_progress_bar.setVisible(False)
        self.main_progress_bar.setStyleSheet(
            f"""
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
        """
        )

        progress_container_layout.addWidget(self.progress_label)
        progress_container_layout.addWidget(self.main_progress_bar)

        # Loading spinner
        self.loading_spinner = LoadingSpinner(24)
        self.loading_spinner.setVisible(False)

        progress_layout.addWidget(self.run_analysis_button)
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
        self.document_display_area.setPlaceholderText(
            "📄 Upload a document to see its content here..."
        )
        self.document_display_area.setReadOnly(True)
        self.document_display_area.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {medical_theme.get_color('bg_secondary')};
                border: 1px solid {medical_theme.get_color('border_light')};
                border-radius: 6px;
                padding: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                line-height: 1.4;
            }}
        """
        )

        document_layout.addWidget(self.document_display_area)
        document_card.add_content(document_content)

        # Right side: Analysis results and AI chat
        results_card = ModernCard("🤖 AI Analysis & Chat")
        results_content = QWidget()
        results_layout = QVBoxLayout(results_content)

        # Results area with rich formatting
        self.analysis_results_area = QTextBrowser()
        self.analysis_results_area.setPlaceholderText(
            """
        🎯 Analysis results will appear here...

        • Upload a clinical document
        • Select an appropriate compliance rubric
        • Click 'Run Analysis' to begin
        • Interact with AI for clarifications
        """
        )
        self.analysis_results_area.setReadOnly(True)
        self.analysis_results_area.setOpenExternalLinks(True)
        self.analysis_results_area.anchorClicked.connect(self.handle_anchor_click)
        self.analysis_results_area.setStyleSheet(
            f"""
            QTextBrowser {{
                background-color: {medical_theme.get_color('bg_primary')};
                border: 1px solid {medical_theme.get_color('border_light')};
                border-radius: 6px;
                padding: 16px;
                font-size: 12px;
                line-height: 1.5;
            }}
        """
        )

        results_layout.addWidget(self.analysis_results_area)
        results_card.add_content(results_content)

        # Add to main layout with responsive splitter
        from src.gui.widgets.responsive_layout import ResponsiveSplitter

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
        self.chat_input.setPlaceholderText(
            "Ask the AI assistant about compliance, documentation, or analysis results..."
        )
        self.chat_input.setMaximumHeight(60)
        self.chat_input.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {medical_theme.get_color('bg_secondary')};
                border: 1px solid {medical_theme.get_color('border_light')};
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
            }}
        """
        )

        # Send button
        self.send_chat_button = AnimatedButton("📤 Send")
        self.send_chat_button.clicked.connect(self.send_chat_message)
        self.send_chat_button.setStyleSheet(
            medical_theme.get_button_stylesheet("primary")
        )
        self.send_chat_button.setFixedWidth(80)

        # Voice input button (future feature)
        self.voice_button = AnimatedButton("🎤")
        self.voice_button.setToolTip("Voice input (coming soon)")
        self.voice_button.setEnabled(False)
        self.voice_button.setFixedWidth(40)
        self.voice_button.setStyleSheet(
            medical_theme.get_button_stylesheet("secondary")
        )

        chat_layout.addWidget(self.chat_input, 1)
        chat_layout.addWidget(self.voice_button)
        chat_layout.addWidget(self.send_chat_button)

        chat_widget.add_content(chat_content)
        return chat_widget

    @staticmethod
    def adapt_layout(breakpoint: str):
        """Adapt layout based on screen size."""
        if breakpoint == "mobile":
            # Stack elements vertically on mobile
            pass
        elif breakpoint == "tablet":
            # Adjust spacing and sizes for tablet
            pass
        # Desktop and large screens use default layout

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
            "All Supported Files (*.pdf *.docx *.txt);;PDF Files (*.pdf);;Word Documents (*.docx);;Text Files (*.txt)",
        )

        if file_name:
            self._current_file_path = file_name

            # Update document status
            file_info = os.path.basename(file_name)
            self.document_status_label.setText(f"📄 {file_info}")

            # Load document content
            try:
                with open(file_name, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    self.document_display_area.setText(
                        content[:5000] + "..." if len(content) > 5000 else content
                    )

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
            from src.core.performance_integration import optimize_for_analysis

            optimization_results = optimize_for_analysis()

            if optimization_results.get("recommendations"):
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
        """Send chat message to AI assistant."""
        message = self.chat_input.toPlainText().strip()
        if not message:
            return

        # Add message to results area
        self.analysis_results_area.append(
            f"""
        <div style="background-color: #e8f4fd; padding: 8px; border-radius: 4px; margin: 4px 0;">
            <strong>You:</strong> {message}
        </div>
        """
        )

        # Clear input
        self.chat_input.clear()

        # TODO: Implement actual AI chat functionality
        self.analysis_results_area.append(
            f"""
        <div style="background-color: #f0f9ff; padding: 8px; border-radius: 4px; margin: 4px 0;">
            <strong>🤖 AI Assistant:</strong> I understand your question about "{message}".
            This feature is being enhanced with the new AI chat system. Please use the analysis results above for now.
        </div>
        """
        )

    # Placeholder methods for existing functionality
    def logout(self):
        raise NotImplementedError()

    def manage_rubrics(self):
        raise NotImplementedError()

    def show_performance_settings(self):
        raise NotImplementedError()

    def show_change_password_dialog(self):
        raise NotImplementedError()

    def show_compliance_guide(self):
        raise NotImplementedError()

    def clear_display(self):
        raise NotImplementedError()

    def handle_anchor_click(self, url):
        raise NotImplementedError()

    def handle_analysis_started(self, task_id):
        raise NotImplementedError()

    def on_analysis_error(self, error):
        raise NotImplementedError()

    def load_ai_models(self):
        raise NotImplementedError()

    def load_dashboard_data(self):
        raise NotImplementedError()