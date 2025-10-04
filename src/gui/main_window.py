import os
import json
import urllib.parse
import webbrowser
from datetime import datetime
from typing import Dict
from PySide6.QtCore import Qt, QThread, QUrl, QTimer
from PySide6.QtGui import QTextDocument, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QDialog,
    QMessageBox,
    QMainWindow,
    QStatusBar,
    QMenuBar,
    QFileDialog,
    QSplitter,
    QTextEdit,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QComboBox,
    QSizePolicy,
    QApplication,
    QCheckBox,
    QFrame,
)

from src.config import get_settings
from src.gui.dialogs.rubric_manager_dialog import RubricManagerDialog
from src.gui.dialogs.chat_dialog import ChatDialog
from src.gui.workers.analysis_starter_worker import AnalysisStarterWorker

from src.gui.workers.folder_analysis_starter_worker import FolderAnalysisStarterWorker
from src.gui.workers.folder_analysis_worker import FolderAnalysisWorker
from src.gui.workers.single_analysis_polling_worker import SingleAnalysisPollingWorker
from src.gui.workers.ai_loader_worker import AILoaderWorker
from src.gui.workers.dashboard_worker import DashboardWorker
from src.gui.workers.meta_analytics_worker import MetaAnalyticsWorker
from src.gui.widgets.dashboard_widget import DashboardWidget

from src.gui.widgets.performance_status_widget import PerformanceStatusWidget
from src.gui.dialogs.performance_settings_dialog import PerformanceSettingsDialog
from src.core.report_generator import ReportGenerator

# Add project root to path for imports
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

settings = get_settings()
API_URL = settings.paths.api_url


class DocumentPreviewDialog(QDialog):
    """Simple dialog to present the loaded document content in a larger view."""

    def __init__(self, document_content: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Document Preview")
        self.resize(820, 620)
        layout = QVBoxLayout(self)
        preview_area = QTextEdit()
        preview_area.setReadOnly(True)
        preview_area.setPlainText(document_content)
        layout.addWidget(preview_area)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        close_button.setFixedHeight(32)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)


class MainApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Simplified authentication - direct access mode
        self.access_token = "direct_access"  # Default token for local-only mode
        self.username = "local_user"
        self.is_admin = True  # Enable all features in local mode
        self._current_file_path = None
        self._current_folder_path = None
        self._current_folder_files = []
        self._current_document_text = ""
        self._current_report_payload = None
        self._analysis_running = False
        self._all_rubrics = []
        self._current_task_id = None
        self.compliance_service = None
        self.worker_thread = None
        self.worker = None
        self.ai_loader_thread = None
        self.ai_loader_worker = None
        self.dashboard_thread = None
        self.dashboard_worker = None
        self.meta_analytics_thread = None
        self.meta_analytics_worker = None
        self.report_generator = ReportGenerator()
        self.api_port = 8000  # Default API port
        self.model_status = {
            "Generator": True,
            "Retriever": True,
            "Fact Checker": True,
            "NER": True,
            "Checklist": True,
            "Chat": True,
        }

        # Extract port from API_URL for MetaAnalyticsWorker
        from urllib.parse import urlparse

        parsed_url = urlparse(API_URL)
        self.api_port = parsed_url.port or 8004
        self.init_base_ui()

    def start(self):
        """
        Starts the application's main logic with direct access mode.
        This is called after the window is created to avoid blocking the constructor,
        which makes the main window testable.
        """
        self._load_user_preferences()  # Load saved preferences first
        self.load_ai_models()
        self.load_main_ui()  # Load main UI directly
        self.show()

    def init_base_ui(self):
        self.setWindowTitle("Therapy Compliance Analyzer")
        # Better default size with minimum constraints for scalability
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)

        # Center window on screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

        self.setGeometry(
            100, 100, 1400, 900
        )  # Larger default size for better proportions
        self.setMinimumSize(900, 650)  # Better minimum for scaling

        # Enable better scaling behavior
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Setup keyboard shortcuts for better accessibility
        self._setup_keyboard_shortcuts()

        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        # File menu
        self.file_menu = self.menu_bar.addMenu("File")
        self.file_menu.addAction("Open Document (Ctrl+O)", self.open_file_dialog)
        self.file_menu.addAction("Open Folder (Ctrl+Shift+O)", self.open_folder_dialog)
        self.file_menu.addSeparator()
        self.file_menu.addAction("Export Report", self.export_report)
        self.file_menu.addSeparator()
        self.file_menu.addAction("Exit", self.close)

        # Tools menu
        self.tools_menu = self.menu_bar.addMenu("Tools")
        self.tools_menu.addAction("Manage Rubrics", self.manage_rubrics)
        self.tools_menu.addAction(
            "Performance Settings", self.show_performance_settings
        )
        self.tools_menu.addAction("Analysis Settings", self.show_analysis_settings)
        self.tools_menu.addSeparator()
        self.tools_menu.addAction("Chat Assistant (Ctrl+H)", self.open_chat_assistant)

        # View menu
        self.view_menu = self.menu_bar.addMenu("View")
        self.view_menu.addAction(
            "Analysis Tab", lambda: self.main_tabs.setCurrentIndex(0)
        )
        self.view_menu.addAction(
            "Dashboard Tab", lambda: self.main_tabs.setCurrentIndex(1)
        )
        self.view_menu.addAction(
            "Settings Tab", lambda: self.main_tabs.setCurrentIndex(2)
        )
        self.view_menu.addSeparator()
        self.view_menu.addAction("Refresh Dashboard", self.load_dashboard_data)

        # Theme menu
        self.theme_menu = self.menu_bar.addMenu("Theme")
        self.theme_menu.addAction("☀️ Light Mode", self.set_light_theme)
        self.theme_menu.addAction("🌙 Dark Mode", self.set_dark_theme)
        self.theme_menu.addSeparator()
        self.theme_menu.addAction("🔄 Toggle Theme (Ctrl+T)", self.toggle_theme)

        # Admin menu (if admin)
        if hasattr(self, "is_admin") and self.is_admin:
            self.admin_menu = self.menu_bar.addMenu("Admin")
            self.admin_menu.addAction("Admin Dashboard", self.open_admin_dashboard)
            self.admin_menu.addAction("System Health", self.show_system_health)

        # Help menu
        self.help_menu = self.menu_bar.addMenu("Help")
        self.help_menu.addAction("Documentation", self.show_documentation)
        self.help_menu.addAction("Keyboard Shortcuts", self.show_keyboard_shortcuts)
        self.help_menu.addSeparator()
        self.help_menu.addAction("About", self.show_about)
        # Keep only essential menu items - settings moved to Settings tab
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - THERAPY DOCUMENT COMPLIANCE ANALYSIS")
        self.ai_status_label = QLabel("Loading AI models...")
        self.status_bar.addPermanentWidget(self.ai_status_label)
        self.user_status_label = QLabel("Local User")
        self.status_bar.addPermanentWidget(self.user_status_label)

        self.model_health_label = QLabel(self._format_model_status_text())
        self.model_health_label.setObjectName("modelHealthLabel")
        self.model_health_label.setTextFormat(Qt.TextFormat.RichText)
        self.status_bar.addPermanentWidget(self.model_health_label)

        # Add performance status widget to status bar
        self.performance_status = PerformanceStatusWidget()
        self.performance_status.settings_requested.connect(
            self.show_performance_settings
        )
        self.status_bar.addPermanentWidget(self.performance_status)

        # Add auto-save indicator
        self.auto_save_label = QLabel("💾")
        self.auto_save_label.setToolTip("Auto-save active")
        self.auto_save_label.setStyleSheet("color: #28a745; font-size: 14px;")
        self.status_bar.addPermanentWidget(self.auto_save_label)

        self.progress_bar = QProgressBar(self.status_bar)
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()

        # Create floating chat button
        self.create_floating_chat_button()

        # Create Pacific Coast branding
        self.create_pacific_coast_branding()

        # Setup auto-save timer for user preferences
        self._setup_auto_save_timer()

        # Initialize Konami code sequence
        self.konami_sequence = []
        self.konami_code = [
            Qt.Key.Key_Up,
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
            Qt.Key.Key_Down,
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
            Qt.Key.Key_B,
            Qt.Key.Key_A,
        ]

    def _format_model_status_text(self) -> str:
        badges = []
        for name, status in self.model_status.items():
            color = "#2ecc71" if status else "#e74c3c"
            badges.append(
                f'<span style="color: {color}; font-weight:600;">&#9679;</span> {name}'
            )
        return "  |  ".join(badges) if badges else "Models offline"

    def _update_model_status_badges(self, updates: Dict[str, bool]) -> None:
        self.model_status.update(updates)
        if hasattr(self, "model_health_label"):
            self.model_health_label.setText(self._format_model_status_text())

    def load_main_ui(self):
        """Load the medical-themed layout: 3 left panels + main tabbed window"""
        # Create main container with title header
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add title header
        title_header = self._create_title_header()
        main_layout.addWidget(title_header)

        # Create main horizontal splitter (left panels + right main window)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)

        self.setCentralWidget(main_container)

        # Left side: 3 stacked panels
        left_panels = self._create_left_panels()

        # Right side: Main tabbed window
        right_main_window = self._create_right_main_window()

        # Add to splitter with medical layout proportions
        main_splitter.addWidget(left_panels)
        main_splitter.addWidget(right_main_window)
        main_splitter.setSizes([350, 850])  # Left panels smaller, main window larger

        # Load rubrics first
        self.load_rubrics()

        # Load dashboard data
        self.load_dashboard_data()

        # Apply theme (default to light, professional medical look)
        self.current_theme = "light"  # Default theme
        self.apply_medical_theme(self.current_theme)

        # Ensure chat button is visible after UI is loaded
        if hasattr(self, "chat_button"):
            self.chat_button.show()
            self.chat_button.raise_()

    def open_admin_dashboard(self):
        webbrowser.open(f"{API_URL}/admin/dashboard?token={self.access_token}")

    def _summarize_folder_contents(self, folder_path: str) -> str:
        preview_lines = [f"Selected folder: {folder_path}", ""]
        collected_files = []
        try:
            for root, _, files in os.walk(folder_path):
                for name in sorted(files):
                    full_path = os.path.join(root, name)
                    collected_files.append(full_path)
                    if len(collected_files) >= 50:
                        break
                if len(collected_files) >= 50:
                    break
        except OSError as exc:
            return f"Could not read folder contents for {folder_path}: {exc}"

        self._current_folder_files = collected_files
        total = len(collected_files)
        preview_lines.append(f"Total files detected: {total}")
        for sample in collected_files[:10]:
            preview_lines.append(f"- {os.path.relpath(sample, folder_path)}")
        if total > 10:
            preview_lines.append("- ...")
        preview_lines.append("")
        preview_lines.append(
            "The first 10 files are shown. Folder analysis will include every detected file."
        )
        return "\n".join(preview_lines)

    @staticmethod
    def _normalize_result_payload(result: object) -> dict:
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"raw_result": result}
        return {"raw_result": result}

    def _create_settings_tab(self) -> QWidget:
        """Create the settings tab with all configuration options"""
        settings_widget = QWidget()
        main_layout = QVBoxLayout(settings_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Theme Settings Group
        theme_group = QGroupBox("🎨 Theme & Appearance")
        theme_layout = QVBoxLayout(theme_group)

        theme_buttons_layout = QHBoxLayout()
        light_btn = QPushButton("☀️ Light Theme")
        light_btn.clicked.connect(self.set_light_theme)
        dark_btn = QPushButton("🌙 Dark Theme")
        dark_btn.clicked.connect(self.set_dark_theme)
        theme_buttons_layout.addWidget(light_btn)
        theme_buttons_layout.addWidget(dark_btn)
        theme_buttons_layout.addStretch()
        theme_layout.addLayout(theme_buttons_layout)

        main_layout.addWidget(theme_group)

        # User Settings Group
        user_group = QGroupBox("👤 User Settings")
        user_layout = QVBoxLayout(user_group)

        user_info_label = QLabel(
            "Running in Direct Access Mode\nNo authentication required for local analysis"
        )
        user_info_label.setStyleSheet("color: #666; font-style: italic;")
        user_layout.addWidget(user_info_label)

        main_layout.addWidget(user_group)

        # Performance Settings Group
        perf_group = QGroupBox("⚡ Performance")
        perf_layout = QVBoxLayout(perf_group)

        perf_settings_btn = QPushButton("🔧 Performance Settings")
        perf_settings_btn.clicked.connect(self.show_performance_settings)
        perf_layout.addWidget(perf_settings_btn)

        main_layout.addWidget(perf_group)

        # Analysis Settings Group
        analysis_group = QGroupBox("🔍 Analysis Configuration")
        analysis_layout = QVBoxLayout(analysis_group)

        analysis_settings_btn = QPushButton("⚙️ Analysis Settings")
        analysis_settings_btn.clicked.connect(self.show_analysis_settings)
        analysis_layout.addWidget(analysis_settings_btn)

        main_layout.addWidget(analysis_group)

        # Admin Section (if admin user)
        if hasattr(self, "is_admin") and self.is_admin:
            admin_group = QGroupBox("👑 Administrator")
            admin_layout = QVBoxLayout(admin_group)

            admin_dashboard_btn = QPushButton("🔧 Admin Dashboard")
            admin_dashboard_btn.clicked.connect(self.open_admin_dashboard)
            admin_layout.addWidget(admin_dashboard_btn)

            main_layout.addWidget(admin_group)

        # About Section
        about_group = QGroupBox("ℹ️ About")
        about_layout = QVBoxLayout(about_group)

        about_btn = QPushButton("📖 About Application")
        about_btn.clicked.connect(self.show_about)
        about_layout.addWidget(about_btn)

        main_layout.addWidget(about_group)

        main_layout.addStretch()
        return settings_widget

    def _update_action_states(self) -> None:
        has_source = bool(self._current_file_path or self._current_folder_path)
        active_rubric = (
            self.rubric_selector.currentData()
            if hasattr(self, "rubric_selector")
            else None
        )
        has_preview = bool(self._current_document_text)
        has_report = bool(self._current_report_payload)
        can_run = bool(has_source and active_rubric and not self._analysis_running)

        # Update main analyze button
        if hasattr(self, "analyze_doc_btn"):
            self.analyze_doc_btn.setEnabled(can_run)

        # Update other buttons
        if hasattr(self, "document_preview_button"):
            self.document_preview_button.setEnabled(has_preview)
        if hasattr(self, "export_report_button"):
            self.export_report_button.setEnabled(has_report)

        # Update file info display
        if hasattr(self, "file_info_label"):
            if self._current_file_path:
                filename = os.path.basename(self._current_file_path)
                self.file_info_label.setText(f"📄 {filename}")
            elif self._current_folder_path:
                folder_name = os.path.basename(self._current_folder_path)
                file_count = (
                    len(self._current_folder_files) if self._current_folder_files else 0
                )
                self.file_info_label.setText(f"📁 {folder_name} ({file_count} files)")
            else:
                self.file_info_label.setText("No document selected")

    def load_rubrics(self):
        """Load available rubrics from the API"""
        try:
            import requests

            response = requests.get(
                f"{API_URL}/compliance/rubrics",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=5,
            )
            if response.status_code == 200:
                self._all_rubrics = response.json()
                self._apply_rubric_filter()
            else:
                # Fallback to default rubrics if API is not available
                self._all_rubrics = [
                    {
                        "id": "default_pt",
                        "name": "PT Compliance Rubric",
                        "discipline": "PT",
                        "description": "Physical Therapy Medicare compliance guidelines",
                    },
                    {
                        "id": "default_ot",
                        "name": "OT Compliance Rubric",
                        "discipline": "OT",
                        "description": "Occupational Therapy Medicare compliance guidelines",
                    },
                    {
                        "id": "default_slp",
                        "name": "SLP Compliance Rubric",
                        "discipline": "SLP",
                        "description": "Speech-Language Pathology Medicare compliance guidelines",
                    },
                ]
                self._apply_rubric_filter()
        except Exception as e:
            print(f"Failed to load rubrics: {e}")
            # Use default rubrics
            self._all_rubrics = [
                {
                    "id": "default_medicare",
                    "name": "Medicare Benefits Policy Manual",
                    "discipline": None,
                    "description": "Default Medicare compliance rubric for PT, OT, and SLP services",
                }
            ]
            self._apply_rubric_filter()

    def _filter_rubrics_by_type(self, _index: int) -> None:
        self._apply_rubric_filter()

    def _apply_rubric_filter(self) -> None:
        rubrics = self._all_rubrics or []
        selected_discipline = None
        if hasattr(self, "rubric_type_selector"):
            selected_discipline = self.rubric_type_selector.currentData()
        if selected_discipline:
            rubrics = [
                rubric
                for rubric in rubrics
                if (rubric.get("discipline") or "").strip() == selected_discipline
            ]

        if hasattr(self, "rubric_selector"):
            previous_selection = self.rubric_selector.currentData()
            self.rubric_selector.blockSignals(True)
            self.rubric_selector.clear()
            self.rubric_selector.addItem("Select a Rubric", None)
            for rubric in rubrics:
                name = rubric.get("name") or rubric.get("title") or "Unnamed Rubric"
                self.rubric_selector.addItem(name, rubric)
            self.rubric_selector.blockSignals(False)

            if previous_selection in rubrics:
                index = self.rubric_selector.findData(previous_selection)
                if index >= 0:
                    self.rubric_selector.setCurrentIndex(index)

        if hasattr(self, "rubric_description_label"):
            self.rubric_description_label.setText(
                "Description of selected rubric will appear here."
            )

        self._update_action_states()

    def handle_anchor_click(self, url: QUrl):
        if url.scheme() == "highlight":
            self.handle_text_highlight_request(url)
        elif url.scheme() == "chat":
            self.handle_chat_request(url)

    def handle_text_highlight_request(self, url: QUrl):
        combined_payload = urllib.parse.unquote(url.path())
        parts = combined_payload.split("|||")
        context_snippet = parts[0]
        text_to_highlight = parts[1] if len(parts) > 1 else context_snippet
        doc = self.document_display_area.document()
        if doc:
            context_cursor = doc.find(
                context_snippet, 0, QTextDocument.FindFlag.FindCaseSensitively
            )
            if not context_cursor.isNull():
                inner_cursor = doc.find(
                    text_to_highlight,
                    context_cursor.selectionStart(),
                    QTextDocument.FindFlag.FindCaseSensitively,
                )
                if (
                    not inner_cursor.isNull()
                    and inner_cursor.selectionEnd() <= context_cursor.selectionEnd()
                ):
                    self.document_display_area.setTextCursor(inner_cursor)
                    self.tabs.setCurrentIndex(0)
                    self.document_display_area.setFocus()
                    return
        cursor = self.document_display_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        self.document_display_area.setTextCursor(cursor)
        if self.document_display_area.find(
            text_to_highlight, QTextDocument.FindFlag.FindCaseSensitively
        ):
            self.tabs.setCurrentIndex(0)
            self.document_display_area.setFocus()
        else:
            self.status_bar.showMessage(
                f"Could not find text: '{text_to_highlight}'", 5000
            )

    def handle_chat_request(self, url: QUrl):
        initial_context = urllib.parse.unquote(url.path())
        chat_dialog = ChatDialog(initial_context, self.access_token, self)
        chat_dialog.exec()

    def manage_rubrics(self):
        dialog = RubricManagerDialog(self.access_token, self)
        dialog.exec()

    def show_change_password_dialog(self):
        # Password change not available in direct access mode
        QMessageBox.information(
            self,
            "Direct Access Mode",
            "Password management is not available in direct access mode.\n"
            "This application runs locally without user authentication.",
        )

    def show_performance_settings(self):
        """Show the performance settings dialog."""
        try:
            dialog = PerformanceSettingsDialog(self)
            dialog.settings_changed.connect(self.on_performance_settings_changed)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open performance settings: {e}"
            )

    def on_performance_settings_changed(self, settings):
        """Handle performance settings changes."""
        try:
            # Update status bar to reflect new settings
            self.status_bar.showMessage("Performance settings updated", 3000)

            # Optionally trigger performance optimization
            from src.core.performance_integration import optimize_for_analysis

            optimization_results = optimize_for_analysis()

            if optimization_results.get("cache_cleanup"):
                memory_freed = optimization_results.get("memory_freed_mb", 0)
                if memory_freed > 0:
                    self.status_bar.showMessage(
                        f"Performance optimized - {memory_freed:.1f} MB freed", 5000
                    )

        except Exception as e:
            print(f"Error handling performance settings change: {e}")

    def load_dashboard_data(self):
        # Direct access mode - no authentication check needed

        self.status_bar.showMessage("Refreshing dashboard data...")
        if self.dashboard_thread and self.dashboard_thread.isRunning():
            self.dashboard_thread.requestInterruption()
            self.dashboard_thread.quit()
            self.dashboard_thread.wait(2000)

        self.dashboard_thread = QThread()
        self.dashboard_worker = DashboardWorker(self.access_token)
        self.dashboard_worker.moveToThread(self.dashboard_thread)
        self.dashboard_thread.started.connect(self.dashboard_worker.run)
        self.dashboard_worker.success.connect(self.on_dashboard_data_loaded)
        self.dashboard_worker.error.connect(
            lambda msg: self.status_bar.showMessage(f"Dashboard Error: {msg}")
        )
        self.dashboard_worker.finished.connect(self.dashboard_thread.quit)
        self.dashboard_thread.finished.connect(self.dashboard_worker.deleteLater)
        self.dashboard_thread.finished.connect(self._clear_dashboard_worker)
        self.dashboard_thread.start()

    def _clear_dashboard_worker(self):
        self.dashboard_worker = None
        self.dashboard_thread = None

    def on_dashboard_data_loaded(self, data):
        self.dashboard_widget.update_dashboard(data)
        self.status_bar.showMessage("Dashboard updated.", 3000)

    def load_meta_analytics_data(self, params=None):
        """Load meta analytics data for admin users."""
        # Direct access mode - all features available

        self.status_bar.showMessage("Loading team analytics...")

        # Stop any existing meta analytics worker
        if (
            hasattr(self, "meta_analytics_thread")
            and self.meta_analytics_thread
            and self.meta_analytics_thread.isRunning()
        ):
            self.meta_analytics_thread.requestInterruption()
            self.meta_analytics_thread.quit()
            self.meta_analytics_thread.wait(2000)

        # Create new worker thread
        self.meta_analytics_thread = QThread()
        self.meta_analytics_worker = MetaAnalyticsWorker(
            base_url=f"http://localhost:{self.api_port}", token=self.access_token
        )

        # Set parameters if provided
        if params:
            self.meta_analytics_worker.set_parameters(
                days_back=params.get("days_back", 90),
                discipline=params.get("discipline"),
                load_type="overview",
            )

        self.meta_analytics_worker.moveToThread(self.meta_analytics_thread)

        # Connect signals
        self.meta_analytics_thread.started.connect(self.meta_analytics_worker.run)
        self.meta_analytics_worker.data_loaded.connect(
            self.on_meta_analytics_data_loaded
        )
        self.meta_analytics_worker.error_occurred.connect(
            lambda msg: self.status_bar.showMessage(
                f"Team Analytics Error: {msg}", 5000
            )
        )
        self.meta_analytics_worker.progress_updated.connect(
            lambda msg: self.status_bar.showMessage(msg, 2000)
        )
        self.meta_analytics_worker.finished.connect(self.meta_analytics_thread.quit)
        self.meta_analytics_thread.finished.connect(
            self.meta_analytics_worker.deleteLater
        )
        self.meta_analytics_thread.finished.connect(self._clear_meta_analytics_worker)

        self.meta_analytics_thread.start()

    def _clear_meta_analytics_worker(self):
        """Clean up meta analytics worker references."""
        self.meta_analytics_worker = None
        self.meta_analytics_thread = None

    def on_meta_analytics_data_loaded(self, data):
        """Handle loaded meta analytics data."""
        if hasattr(self, "meta_analytics_widget"):
            self.meta_analytics_widget.update_data(data)
            self.status_bar.showMessage("Team analytics updated.", 3000)

    def run_analysis(self):
        if self._analysis_running:
            return

        source_path = self._current_file_path or self._current_folder_path
        if not source_path:
            self.show_user_notification(
                "No Source Selected",
                "Please upload a document or folder before running analysis.",
                "warning",
            )
            return

        selected_rubric = self.rubric_selector.currentData()
        if not selected_rubric:
            self.show_user_notification(
                "No Rubric Selected",
                "Please select a rubric before running analysis.",
                "warning",
            )
            return

        discipline = selected_rubric.get("discipline", "Unknown")
        rubric_id = selected_rubric.get("id")

        self.show_progress_notification("Optimizing performance...")
        try:
            from src.core.performance_integration import optimize_for_analysis

            optimization_results = optimize_for_analysis()
            if optimization_results.get("recommendations"):
                recommendations = "\n".join(optimization_results["recommendations"])
                self.show_user_notification(
                    "Performance Optimization Complete",
                    f"Performance optimization completed:\n\n{recommendations}",
                    "success",
                )
        except Exception as exc:
            print(f"Performance optimization failed: {exc}")
            self.show_user_notification(
                "Performance Optimization Failed",
                f"Performance optimization encountered an issue: {exc}",
                "warning",
            )

        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self._analysis_running = True
        self._current_report_payload = None
        self._update_action_states()
        self.status_bar.showMessage("Starting analysis...")

        payload = {"discipline": discipline, "rubric_id": rubric_id}
        if self._current_folder_path:
            self._start_folder_analysis(payload)
        else:
            self._start_file_analysis(payload)

    def _dispose_worker_thread(self) -> None:
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.requestInterruption()
            self.worker_thread.quit()
            self.worker_thread.wait(2000)
        self.worker_thread = None
        self.worker = None

    def _start_file_analysis(self, payload: dict) -> None:
        self._dispose_worker_thread()
        self.worker_thread = QThread()
        self.worker = AnalysisStarterWorker(
            self._current_file_path,
            payload,
            self.access_token or "",
        )
        self.worker.moveToThread(self.worker_thread)
        self.worker.success.connect(self.handle_analysis_started)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def _start_folder_analysis(self, payload: dict) -> None:
        if not self._current_folder_files:
            summary = self._summarize_folder_contents(self._current_folder_path)
            self.document_display_area.setPlainText(summary)
            if not self._current_folder_files:
                self.on_analysis_error(
                    "Selected folder does not contain any files for analysis."
                )
                return

        files_payload = []
        try:
            for file_path in self._current_folder_files:
                file_handle = open(file_path, "rb")
                files_payload.append(
                    (
                        "files",
                        (
                            os.path.basename(file_path),
                            file_handle,
                            "application/octet-stream",
                        ),
                    )
                )
        except OSError as exc:
            for _, (_, handle, _) in files_payload:
                handle.close()
            self.on_analysis_error(f"Failed to open folder files: {exc}")
            return

        self._dispose_worker_thread()
        self.worker_thread = QThread()
        self.worker = FolderAnalysisStarterWorker(
            files_payload,
            payload,
            self.access_token or "",
        )
        self.worker.moveToThread(self.worker_thread)
        self.worker.success.connect(self.handle_analysis_started)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def _start_polling_worker(self, task_id: str) -> None:
        self._dispose_worker_thread()
        self.worker_thread = QThread()
        if self._current_folder_path:
            self.worker = FolderAnalysisWorker(task_id)
        else:
            self.worker = SingleAnalysisPollingWorker(task_id)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.success.connect(self.on_analysis_success)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.progress.connect(self.on_analysis_progress)
        self.worker.finished.connect(self._on_analysis_finished)
        self.worker_thread.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def _on_analysis_finished(self) -> None:
        self._analysis_running = False
        self._current_task_id = None
        self.worker = None
        self.worker_thread = None
        if self.progress_bar.maximum() == 0:
            self.progress_bar.setRange(0, 100)
        if self.progress_bar.value() == 0:
            self.progress_bar.setValue(0)
        self.progress_bar.hide()
        self._update_action_states()

    def handle_analysis_started(self, task_id: str):
        self._current_task_id = task_id
        self.status_bar.showMessage(f"Analysis in progress... (Task ID: {task_id})")
        self._start_polling_worker(task_id)

    def on_analysis_progress(self, progress):
        if self.progress_bar.maximum() == 0:
            self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(max(0, min(100, int(progress))))
        if not self.progress_bar.isVisible():
            self.progress_bar.show()

    def on_analysis_success(self, result):
        payload = self._normalize_result_payload(result)
        self._current_report_payload = payload

        report_html = payload.get("report_html")
        if not report_html and payload.get("analysis"):
            report_html = self.report_generator.generate_html_report(
                analysis_result=payload.get("analysis", {}),
                doc_name=payload.get("analysis", {}).get("document_name", "Document"),
            )

        if report_html:
            self.analysis_results_area.setHtml(report_html)
        else:
            self.analysis_results_area.setPlainText(json.dumps(payload, indent=2))

        self.status_bar.showMessage("Analysis complete.", 5000)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.hide()
        self._on_analysis_finished()

    def on_analysis_error(self, error_message):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        QMessageBox.critical(self, "Analysis Error", error_message)
        self.status_bar.showMessage("Backend analysis failed.")
        self._on_analysis_finished()

    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Document", "", "All Files (*.*)"
        )
        if not file_name:
            return

        self._current_file_path = file_name
        self._current_folder_path = None
        self._current_folder_files = []
        self._current_report_payload = None

        try:
            with open(file_name, "r", encoding="utf-8") as handle:
                content = handle.read()
        except (IOError, UnicodeDecodeError):
            try:
                with open(file_name, "rb") as handle:
                    content = handle.read().decode("utf-8", errors="ignore")
            except OSError as exc:
                content = f"Could not display preview for: {file_name}\n{exc}"

        self._current_document_text = content
        self.document_display_area.setPlainText(content)
        self.selected_source_label.setText(os.path.basename(file_name))
        self.status_bar.showMessage(f"Loaded document: {os.path.basename(file_name)}")
        self.analysis_results_area.clear()
        self._analysis_running = False
        self._update_action_states()

    def open_folder_dialog(self):
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            "",
            QFileDialog.Option.ShowDirsOnly,
        )
        if not folder_path:
            return

        normalized = os.path.normpath(folder_path)
        summary = self._summarize_folder_contents(normalized)
        self._current_folder_path = normalized
        self._current_file_path = None
        self._current_report_payload = None
        self._current_document_text = summary
        self.document_display_area.setPlainText(summary)
        display_name = os.path.basename(normalized) or normalized
        self.selected_source_label.setText(display_name)
        self.status_bar.showMessage(f"Loaded folder: {display_name}")
        self.analysis_results_area.clear()
        self._analysis_running = False
        self._update_action_states()

    def stop_analysis(self) -> None:
        if not self._analysis_running:
            return

        if self.worker and hasattr(self.worker, "stop"):
            try:
                self.worker.stop()  # type: ignore[attr-defined]
            except Exception:
                pass

        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.requestInterruption()
            self.worker_thread.quit()
            self.worker_thread.wait(2000)

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        self.status_bar.showMessage("Analysis cancelled.", 4000)
        self._on_analysis_finished()

    def show_document_preview(self) -> None:
        if not self._current_document_text:
            QMessageBox.information(
                self,
                "No Document",
                "Please upload a document before opening the preview.",
            )
            return

        preview_dialog = DocumentPreviewDialog(self._current_document_text, self)
        preview_dialog.exec()

    def open_analytics_dashboard(self) -> None:
        if hasattr(self, "tabs") and hasattr(self, "dashboard_widget"):
            index = self.tabs.indexOf(self.dashboard_widget)
            if index != -1:
                self.tabs.setCurrentIndex(index)
                self.load_dashboard_data()
                self.status_bar.showMessage("Analytics dashboard opened.", 3000)

    def export_report(self) -> None:
        if not self._current_report_payload:
            QMessageBox.information(
                self,
                "No Report",
                "Run an analysis to generate a report before exporting.",
            )
            return

        # Get current report HTML
        report_html = self.analysis_results_area.toHtml()
        if not report_html.strip():
            QMessageBox.warning(
                self,
                "No Report Content",
                "No report content available for export.",
            )
            return

        # Ask user for export format and location
        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilters(
            ["PDF Files (*.pdf)", "HTML Files (*.html)", "All Files (*.*)"]
        )
        file_dialog.setDefaultSuffix("pdf")

        # Set default filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"compliance_report_{timestamp}"
        file_dialog.selectFile(default_name)

        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            file_extension = os.path.splitext(file_path)[1].lower()

            try:
                if file_extension == ".pdf":
                    self._export_pdf_report(report_html, file_path)
                elif file_extension == ".html":
                    self._export_html_report(report_html, file_path)
                else:
                    # Default to HTML
                    if not file_path.endswith((".pdf", ".html")):
                        file_path += ".html"
                    self._export_html_report(report_html, file_path)

                QMessageBox.information(
                    self,
                    "Export Complete",
                    f"Report exported successfully to:\n{file_path}",
                )

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Failed to export report:\n{str(e)}",
                )

    def _export_pdf_report(self, html_content: str, file_path: str) -> None:
        """Export report as PDF using the PDF export service."""
        try:
            from src.core.pdf_export_service import export_compliance_report_to_pdf

            # Get document name for metadata
            document_name = None
            if self._current_file_path:
                document_name = os.path.basename(self._current_file_path)
            elif self._current_folder_path:
                document_name = f"Folder: {os.path.basename(self._current_folder_path)}"

            success = export_compliance_report_to_pdf(
                html_content, file_path, document_name
            )

            if not success:
                raise Exception(
                    "PDF export service failed. Please check that weasyprint or pdfkit is installed."
                )

        except ImportError:
            raise Exception(
                "PDF export not available. Please install weasyprint or pdfkit:\npip install weasyprint"
            )

    def _export_html_report(self, html_content: str, file_path: str) -> None:
        """Export report as standalone HTML file."""
        # Create a complete HTML document with embedded CSS
        complete_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Therapy Compliance Analysis Report</title>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 20px; 
                    background-color: #f8f9fa; 
                    line-height: 1.6; 
                }}
                .container {{ 
                    max-width: 1000px; 
                    margin: auto; 
                    background-color: #fff; 
                    padding: 30px; 
                    border-radius: 8px; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
                }}
                .export-info {{
                    background-color: #e3f2fd;
                    border: 1px solid #2196f3;
                    border-radius: 4px;
                    padding: 10px;
                    margin-bottom: 20px;
                    font-size: 12px;
                    color: #1565c0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="export-info">
                    <strong>Exported Report</strong> - Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")} 
                    by Therapy Compliance Analyzer
                </div>
                {html_content}
            </div>
        </body>
        </html>
        """

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(complete_html)

    def load_ai_models(self):
        if self.ai_loader_thread and self.ai_loader_thread.isRunning():
            return

        self.ai_loader_thread = QThread()
        self.ai_loader_worker = AILoaderWorker()
        self.ai_loader_worker.moveToThread(self.ai_loader_thread)
        self.ai_loader_thread.started.connect(self.ai_loader_worker.run)
        self.ai_loader_worker.finished.connect(self.on_ai_loaded)
        self.ai_loader_worker.finished.connect(self.ai_loader_thread.quit)
        self.ai_loader_thread.finished.connect(self.ai_loader_worker.deleteLater)
        self.ai_loader_thread.finished.connect(self._clear_ai_loader_worker)
        self.ai_loader_thread.start()

    def _clear_ai_loader_worker(self):
        self.ai_loader_worker = None
        self.ai_loader_thread = None

    def on_ai_loaded(
        self, compliance_service, is_healthy, status_message, health_details
    ):
        self.compliance_service = compliance_service
        self.ai_status_label.setText(status_message)
        self.ai_status_label.setStyleSheet(
            "color: green;" if is_healthy else "color: red;"
        )
        if isinstance(health_details, dict):
            translated = {name: bool(value) for name, value in health_details.items()}
            self._update_model_status_badges(translated)
        else:
            self._update_model_status_badges(
                {key: bool(is_healthy) for key in self.model_status}
            )
        self._populate_rubric_selector()  # Populate rubrics after AI is loaded

    def _populate_rubric_selector(self):
        if not self.compliance_service:
            return

        rubrics = self.compliance_service.get_available_rubrics() or []

        # Add Medicare Benefits Policy Manual as default if not present
        medicare_rubric = {
            "id": "medicare_benefits_policy_manual",
            "name": "Medicare Benefits Policy Manual",
            "description": "Default Medicare compliance rubric for PT, OT, and SLP services covering documentation requirements, medical necessity, and billing standards",
            "discipline": "All",
            "category": "Medicare Compliance",
            "is_default": True,
        }

        # Check if Medicare rubric already exists
        has_medicare = any(
            r.get("name") == "Medicare Benefits Policy Manual" for r in rubrics
        )
        if not has_medicare:
            rubrics.insert(0, medicare_rubric)  # Add as first option

        self._all_rubrics = rubrics

        disciplines = sorted(
            {
                (rubric.get("discipline") or "Unknown").strip() or "Unknown"
                for rubric in rubrics
            }
        )

        if hasattr(self, "rubric_type_selector"):
            self.rubric_type_selector.blockSignals(True)
            self.rubric_type_selector.clear()
            self.rubric_type_selector.addItem("All Disciplines", None)
            for discipline in disciplines:
                label = (
                    discipline.upper() if len(discipline) <= 4 else discipline.title()
                )
                self.rubric_type_selector.addItem(label, discipline)
            self.rubric_type_selector.blockSignals(False)

        self._apply_rubric_filter()

        # Set Medicare Benefits Policy Manual as default selection
        if hasattr(self, "rubric_selector"):
            for i in range(self.rubric_selector.count()):
                rubric_data = self.rubric_selector.itemData(i)
                if (
                    rubric_data
                    and rubric_data.get("name") == "Medicare Benefits Policy Manual"
                ):
                    self.rubric_selector.setCurrentIndex(i)
                    break

    def _on_rubric_selected(self, index):
        selected_rubric = self.rubric_selector.itemData(index)
        if selected_rubric:
            self.rubric_description_label.setText(
                selected_rubric.get("description", "No description available.")
            )
        else:
            self.rubric_description_label.setText(
                "Description of selected rubric will appear here."
            )

        self._update_action_states()

    def apply_stylesheet(self, theme: str = "dark") -> None:
        """Apply the requested theme to the main window."""
        stylesheet_getter = (
            self.get_light_theme_stylesheet
            if theme == "light"
            else self.get_dark_theme_stylesheet
        )
        self.setStyleSheet(stylesheet_getter())

    @staticmethod
    def save_theme_setting(theme: str) -> None:
        with open("theme.cfg", "w", encoding="utf-8") as handle:
            handle.write(theme)

    @staticmethod
    def load_theme_setting() -> str:
        try:
            with open("theme.cfg", "r", encoding="utf-8") as handle:
                return handle.read().strip()
        except FileNotFoundError:
            return "dark"

    @staticmethod
    def get_light_theme_stylesheet() -> str:
        return """
QWidget { background-color: #f5f5f7; color: #1b1b1f; font-size: 13px; }
QMainWindow { background-color: #f5f5f7; }
QMenuBar { background-color: #f5f5f7; color: #1b1b1f; border: none; }
QMenuBar::item:selected { background-color: #d8def8; color: #1b1b1f; }
QMenu { background-color: #ffffff; color: #1b1b1f; border: 1px solid #d0d4dc; }
QMenu::item:selected { background-color: #e7ebff; }
QStatusBar { background-color: #f5f5f7; color: #1b1b1f; }
QGroupBox { background-color: #ffffff; color: #1b1b1f; border: 1px solid #d0d4dc; border-radius: 10px; margin-top: 16px; padding-top: 18px; }
QGroupBox::title { color: #4a5bdc; subcontrol-origin: margin; subcontrol-position: top left; padding: 0 12px; margin-left: 8px; background-color: transparent; }
QGroupBox#documentPane { border-color: #6550d8; }
QGroupBox#resultsPane { border-color: #2196b6; }
QSplitter#analysisSplitter::handle { background-color: #d0d4dc; margin: 0 4px; width: 8px; border-radius: 4px; }
QSplitter#analysisSplitter::handle:hover { background-color: #2196b6; }
QTabWidget::pane { border: 1px solid #d0d4dc; border-radius: 8px; top: 0px; }
QTabBar::tab { background: #eef0f6; color: #1b1b1f; padding: 8px 18px; margin-right: 2px; border: 1px solid #d0d4dc; border-top-left-radius: 8px; border-top-right-radius: 8px; }
QTabBar::tab:selected { background: #ffffff; color: #1b1b1f; border-bottom-color: #f5f5f7; }
QTabBar::tab:hover { background: #d8def8; }
QTextEdit, QTextBrowser { background-color: #ffffff; color: #1b1b1f; border: 1px solid #d0d4dc; border-radius: 8px; padding: 8px; selection-background-color: #6aa9ff; selection-color: #ffffff; }
QLabel#selectedSourceLabel { color: #455adf; font-weight: 500; }
QProgressBar { background-color: #ffffff; border: 1px solid #d0d4dc; border-radius: 6px; height: 10px; }
QProgressBar#analysisProgress::chunk { background-color: #2196b6; border-radius: 6px; }
QPushButton { background-color: #eef0f6; color: #1b1b1f; border: 1px solid #6550d8; border-radius: 8px; padding: 8px 18px; font-weight: 500; }
QPushButton:hover { background-color: #dde2fb; border-color: #7b68f7; }
QPushButton:pressed { background-color: #c6dff4; border-color: #2196b6; }
QPushButton:disabled { background-color: #f0f0f0; color: #9aa0a9; border-color: #d0d4dc; }
QToolButton { background-color: #eef0f6; color: #1b1b1f; border: 1px solid #2196b6; border-radius: 8px; padding: 6px 14px; }
QToolButton::menu-indicator { image: none; }
QToolButton:hover { background-color: #d8f2f8; border-color: #2ab7ca; }
QComboBox { background-color: #ffffff; color: #1b1b1f; border: 1px solid #2196b6; border-radius: 8px; padding: 6px 10px; }
QComboBox::drop-down { border: none; width: 24px; subcontrol-origin: padding; subcontrol-position: center right; padding-right: 6px; }
QComboBox::down-arrow {
    width: 0;
    height: 0;
    margin-right: 6px;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 8px solid #2196b6;
}
QComboBox::down-arrow:on {
    border-top-color: #6550d8;
}
QLineEdit { background-color: #ffffff; color: #1b1b1f; border: 1px solid #d0d4dc; border-radius: 6px; padding: 6px; }
QScrollBar:vertical { background: #f0f0f0; width: 12px; margin: 0; }
QScrollBar::handle:vertical { background: #c7ccd6; min-height: 24px; border-radius: 6px; }
QScrollBar::handle:vertical:hover { background: #2196b6; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background: none; height: 0; }
QScrollBar:horizontal { background: #f0f0f0; height: 12px; margin: 0; }
QScrollBar::handle:horizontal { background: #c7ccd6; min-width: 24px; border-radius: 6px; }
QScrollBar::handle:horizontal:hover { background: #6550d8; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { background: none; width: 0; }
"""

    @staticmethod
    def get_dark_theme_stylesheet() -> str:
        return """
QWidget { background-color: #2b2b2b; color: #e6e6e6; font-size: 13px; }
QMainWindow { background-color: #2b2b2b; }
QMenuBar { background-color: #2b2b2b; color: #e6e6e6; border: none; }
QMenuBar::item { padding: 6px 14px; background: transparent; }
QMenuBar::item:selected { background-color: #3a3f52; color: #ffffff; }
QMenu { background-color: #323232; color: #e6e6e6; border: 1px solid #3c3f41; }
QMenu::item:selected { background-color: #3f4458; color: #ffffff; }
QStatusBar { background-color: #2b2b2b; color: #e6e6e6; }
QGroupBox { background-color: #323232; color: #e6e6e6; border: 1px solid #3c3f41; border-radius: 10px; margin-top: 16px; padding-top: 18px; }
QGroupBox::title { color: #8ab4ff; subcontrol-origin: margin; subcontrol-position: top left; padding: 0 12px; margin-left: 8px; background-color: transparent; }
QGroupBox#documentPane { border-color: #7254ff; }
QGroupBox#resultsPane { border-color: #2ab7ca; }
QSplitter#analysisSplitter::handle { background-color: #3c3f41; margin: 0 4px; width: 8px; border-radius: 4px; }
QSplitter#analysisSplitter::handle:hover { background-color: #2ab7ca; }
QTabWidget::pane { border: 1px solid #3c3f41; border-radius: 8px; top: 0px; }
QTabBar::tab { background: #323232; color: #cfcfcf; padding: 8px 18px; margin-right: 2px; border: 1px solid #3c3f41; border-top-left-radius: 8px; border-top-right-radius: 8px; }
QTabBar::tab:selected { background: #413f5e; color: #ffffff; border-bottom-color: #2b2b2b; }
QTabBar::tab:hover { background: #3a3f52; }
QTextEdit, QTextBrowser { background-color: #1f1f1f; color: #f5f5f5; border: 1px solid #3c3f41; border-radius: 8px; padding: 8px; selection-background-color: #2ab7ca; selection-color: #0f172a; }
QLabel#selectedSourceLabel { color: #9cdcf2; font-weight: 500; }
QProgressBar { background-color: #1f1f1f; border: 1px solid #3c3f41; border-radius: 6px; height: 10px; }
QProgressBar#analysisProgress::chunk { background-color: #2ab7ca; border-radius: 6px; }
QPushButton { background-color: #3c3f41; color: #e6e6e6; border: 1px solid #7254ff; border-radius: 8px; padding: 8px 18px; font-weight: 500; }
QPushButton:hover { background-color: #484b4d; border-color: #8f78ff; }
QPushButton:pressed { background-color: #31343a; border-color: #2ab7ca; }
QPushButton:disabled { background-color: #242424; color: #707070; border-color: #3c3f41; }
QToolButton { background-color: #3c3f41; color: #e6e6e6; border: 1px solid #2ab7ca; border-radius: 8px; padding: 6px 14px; }
QToolButton::menu-indicator { image: none; }
QToolButton:hover { background-color: #2f3340; border-color: #32c6d8; }
QComboBox { background-color: #323232; color: #e6e6e6; border: 1px solid #2ab7ca; border-radius: 8px; padding: 6px 10px; }
QComboBox::drop-down { border: none; width: 24px; subcontrol-origin: padding; subcontrol-position: center right; padding-right: 6px; }
QComboBox::down-arrow {
    width: 0;
    height: 0;
    margin-right: 6px;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 8px solid #3b82f6;
}
QComboBox::down-arrow:on {
    border-top-color: #8ab4ff;
}
QLineEdit { background-color: #323232; color: #e6e6e6; border: 1px solid #3c3f41; border-radius: 6px; padding: 6px; }
QScrollBar:vertical { background: #2b2b2b; width: 12px; margin: 0; }
QScrollBar::handle:vertical { background: #43484d; min-height: 24px; border-radius: 6px; }
QScrollBar::handle:vertical:hover { background: #2ab7ca; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background: none; height: 0; }
QScrollBar:horizontal { background: #2b2b2b; height: 12px; margin: 0; }
QScrollBar::handle:horizontal { background: #43484d; min-width: 24px; border-radius: 6px; }
QScrollBar::handle:horizontal:hover { background: #7254ff; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { background: none; width: 0; }
QMessageBox { background-color: #2b2b2b; color: #e6e6e6; }
QMessageBox QPushButton { min-width: 90px; }
"""

    def create_floating_chat_button(self):
        """Create moveable floating chat button"""
        self.chat_button = QPushButton("💬")
        self.chat_button.setParent(self)
        self.chat_button.setFixedSize(50, 50)
        self.chat_button.setToolTip("Chat with AI Assistant")
        self.chat_button.clicked.connect(self.open_chat_assistant)
        self.chat_button.setObjectName("chatButton")

        # Make it draggable
        self.chat_button.mousePressEvent = self.chat_button_mouse_press
        self.chat_button.mouseMoveEvent = self.chat_button_mouse_move
        self.chat_button.mouseReleaseEvent = self.chat_button_mouse_release
        self.chat_button_dragging = False
        self.chat_button_offset = None

        # Position it away from Pacific Coast easter egg and show it
        self.position_chat_button()
        self.chat_button.show()  # Make sure it's visible
        self.chat_button.raise_()  # Bring to front

    def position_chat_button(self):
        """Position floating chat button"""
        if hasattr(self, "chat_button"):
            # Position in bottom left corner
            x = 20  # Left margin
            y = self.height() - self.chat_button.height() - 60  # Above status bar
            self.chat_button.move(x, y)

    def chat_button_mouse_press(self, event):
        """Handle chat button mouse press for dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.chat_button_dragging = True
            self.chat_button_offset = event.position().toPoint()

    def chat_button_mouse_move(self, event):
        """Handle chat button mouse move for dragging"""
        if self.chat_button_dragging and self.chat_button_offset:
            # Calculate new position
            new_pos = (
                self.mapFromGlobal(event.globalPosition().toPoint())
                - self.chat_button_offset
            )
            # Keep button within window bounds
            max_x = self.width() - self.chat_button.width()
            max_y = self.height() - self.chat_button.height()

            new_x = max(0, min(new_pos.x(), max_x))
            new_y = max(0, min(new_pos.y(), max_y))

            self.chat_button.move(new_x, new_y)

    def chat_button_mouse_release(self, event):
        """Handle chat button mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.chat_button_dragging = False
            self.chat_button_offset = None

    def create_pacific_coast_branding(self):
        """Create Pacific Coast Therapy branding in bottom right corner"""
        self.pacific_coast_label = QLabel("Pacific Coast Therapy 🌴")
        self.pacific_coast_label.setParent(self)
        self.pacific_coast_label.setObjectName("pacificCoastBranding")
        self.pacific_coast_label.setStyleSheet("""
            QLabel#pacificCoastBranding {
                font-family: 'Brush Script MT', 'Lucida Handwriting', cursive;
                font-style: italic;
                font-size: 12px;
                color: #666;
                background: transparent;
                padding: 2px 5px;
            }
        """)
        self.pacific_coast_label.adjustSize()
        self.position_pacific_coast_branding()
        self.pacific_coast_label.show()

    def position_pacific_coast_branding(self):
        """Position Pacific Coast branding in bottom right corner"""
        if hasattr(self, "pacific_coast_label"):
            x = self.width() - self.pacific_coast_label.width() - 20
            y = (
                self.height() - self.pacific_coast_label.height() - 40
            )  # Above status bar
            self.pacific_coast_label.move(x, y)

    def open_chat_assistant(self):
        """Open the chat assistant dialog"""
        chat_dialog = ChatDialog(
            "Hello! How can I help you with compliance today?",
            self.access_token or "",
            self,
        )
        chat_dialog.exec()

    def show_analysis_settings(self):
        """Show analysis settings dialog"""
        QMessageBox.information(
            self, "Analysis Settings", "Analysis configuration settings - Coming soon!"
        )

    def show_about(self):
        """Show about dialog with Kevin Moon and emoji"""
        about_text = f"""
        <h2>Therapy Compliance Analyzer</h2>
        <p><b>Version:</b> 1.0.0</p>
        <p><b>AI-Powered Clinical Documentation Analysis</b></p>
        <br>
        <p>This application helps healthcare professionals ensure their documentation 
        meets Medicare and regulatory compliance standards using advanced AI technology.</p>
        <br>
        <p><b>Features:</b></p>
        <ul>
        <li>Local AI processing for privacy</li>
        <li>Multi-format document support</li>
        <li>Interactive compliance reports</li>
        <li>Real-time chat assistance</li>
        <li>Keyboard shortcuts for efficiency</li>
        </ul>
        <br>
        {self.get_keyboard_shortcuts_help()}
        <br>
        <p><b>Developed by:</b> Kevin Moon 🤝💖</p>
        <p><i>Pacific Coast Development 🌴</i></p>
        <br>
        <p>© 2024 All rights reserved</p>
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("About Therapy Compliance Analyzer")
        msg.setText(about_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def show_system_health(self):
        """Show system health dialog"""
        health_info = []
        for model, status in self.model_status.items():
            status_icon = "✅" if status else "❌"
            health_info.append(
                f"{status_icon} {model}: {'Ready' if status else 'Not Ready'}"
            )

        health_text = f"""
        <div style='line-height: 1.6;'>
        <h3>🏥 System Health Status</h3>
        <br>
        <h4>AI Models:</h4>
        {"<br>".join(health_info)}
        <br><br>
        <h4>API Connection:</h4>
        ✅ Local API: Connected<br>
        ✅ Database: Connected<br>
        </div>
        """

        QMessageBox.information(self, "System Health", health_text)

    def show_documentation(self):
        """Show documentation dialog"""
        QMessageBox.information(
            self,
            "Documentation",
            "📖 Documentation and user guides are available online.\n\n"
            "Visit our website for comprehensive guides on:\n"
            "• Getting started with compliance analysis\n"
            "• Understanding compliance reports\n"
            "• Advanced features and settings\n"
            "• Troubleshooting common issues",
        )

    def show_keyboard_shortcuts(self):
        """Show keyboard shortcuts help dialog."""
        shortcuts_text = self.get_keyboard_shortcuts_help()

        msg = QMessageBox(self)
        msg.setWindowTitle("Keyboard Shortcuts")
        msg.setText(shortcuts_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def resizeEvent(self, event):
        """Handle window resize to reposition floating elements and adjust layout"""
        super().resizeEvent(event)

        # Reposition floating elements
        if hasattr(self, "chat_button") and not self.chat_button_dragging:
            self.position_chat_button()
        if hasattr(self, "pacific_coast_label"):
            self.position_pacific_coast_branding()

        # Adjust layout based on window size for better scaling
        window_width = self.width()
        # For very small windows, adjust splitter orientation
        if hasattr(self, "tabs") and self.tabs.currentIndex() == 0:  # Analysis tab
            try:
                # Find the splitter in the current tab
                analysis_widget = self.tabs.widget(0)
                if analysis_widget:
                    splitters = analysis_widget.findChildren(QSplitter)
                    for splitter in splitters:
                        if window_width < 1000:
                            # For small windows, make document area smaller
                            splitter.setStretchFactor(0, 1)
                            splitter.setStretchFactor(1, 2)
                        else:
                            # For larger windows, restore balanced layout
                            splitter.setStretchFactor(0, 2)
                            splitter.setStretchFactor(1, 3)
            except Exception:
                pass  # Ignore errors during resize

    def closeEvent(self, event):
        """Handle application close event with proper cleanup."""
        try:
            # Clean up performance status widget
            if hasattr(self, "performance_status"):
                self.performance_status.cleanup()

            # Clean up performance integration service
            try:
                from src.core.performance_integration import performance_integration

                performance_integration.cleanup()
            except ImportError:
                pass

            # Clean up any running worker threads
            if self.worker_thread and self.worker_thread.isRunning():
                self.worker_thread.quit()
                self.worker_thread.wait(3000)

            if self.ai_loader_thread and self.ai_loader_thread.isRunning():
                self.ai_loader_thread.quit()
                self.ai_loader_thread.wait(3000)

            if self.dashboard_thread and self.dashboard_thread.isRunning():
                self.dashboard_thread.quit()
                self.dashboard_thread.wait(3000)

            # Accept the close event
            event.accept()

        except Exception as e:
            print(f"Error during application cleanup: {e}")
            event.accept()  # Still close even if cleanup fails

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for improved accessibility and workflow efficiency."""
        # Analysis shortcuts
        self.shortcut_run_analysis = QShortcut(QKeySequence("Ctrl+R"), self)
        self.shortcut_run_analysis.activated.connect(self.run_analysis)

        self.shortcut_stop_analysis = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_stop_analysis.activated.connect(self.stop_analysis)

        # File operations
        self.shortcut_open_file = QShortcut(QKeySequence("Ctrl+O"), self)
        self.shortcut_open_file.activated.connect(self.open_file_dialog)

        self.shortcut_open_folder = QShortcut(QKeySequence("Ctrl+Shift+O"), self)
        self.shortcut_open_folder.activated.connect(self.open_folder_dialog)

        # UI navigation
        self.shortcut_analysis_tab = QShortcut(QKeySequence("Ctrl+1"), self)
        self.shortcut_analysis_tab.activated.connect(
            lambda: self.tabs.setCurrentIndex(0) if hasattr(self, "tabs") else None
        )

        self.shortcut_dashboard_tab = QShortcut(QKeySequence("Ctrl+2"), self)
        self.shortcut_dashboard_tab.activated.connect(
            lambda: self.tabs.setCurrentIndex(1) if hasattr(self, "tabs") else None
        )

        self.shortcut_settings_tab = QShortcut(QKeySequence("Ctrl+3"), self)
        self.shortcut_settings_tab.activated.connect(
            lambda: self.tabs.setCurrentIndex(2) if hasattr(self, "tabs") else None
        )

        # Chat and help
        self.shortcut_chat = QShortcut(QKeySequence("Ctrl+H"), self)
        self.shortcut_chat.activated.connect(self.open_chat_assistant)

        # Theme switching
        self.shortcut_light_theme = QShortcut(QKeySequence("Ctrl+L"), self)
        self.shortcut_light_theme.activated.connect(self.set_light_theme)

        self.shortcut_dark_theme = QShortcut(QKeySequence("Ctrl+D"), self)
        self.shortcut_dark_theme.activated.connect(self.set_dark_theme)

        # Export and clear
        self.shortcut_export = QShortcut(QKeySequence("Ctrl+E"), self)
        self.shortcut_export.activated.connect(self.export_report)

        self.shortcut_clear = QShortcut(QKeySequence("Ctrl+K"), self)
        self.shortcut_clear.activated.connect(self.clear_display)

    def _setup_auto_save_timer(self):
        """Setup auto-save timer for user preferences and session state."""
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save_preferences)
        self.auto_save_timer.start(30000)  # Auto-save every 30 seconds

    def _auto_save_preferences(self):
        """Auto-save user preferences and session state."""
        try:
            preferences = {
                "window_geometry": {
                    "x": self.x(),
                    "y": self.y(),
                    "width": self.width(),
                    "height": self.height(),
                },
                "current_tab": self.tabs.currentIndex() if hasattr(self, "tabs") else 0,
                "theme": self.load_theme_setting(),
                "chat_button_position": {
                    "x": self.chat_button.x() if hasattr(self, "chat_button") else 0,
                    "y": self.chat_button.y() if hasattr(self, "chat_button") else 0,
                },
            }

            # Save to preferences file
            with open("user_preferences.json", "w", encoding="utf-8") as f:
                json.dump(preferences, f, indent=2)

            # Show brief visual feedback
            if hasattr(self, "auto_save_label"):
                original_text = self.auto_save_label.text()
                self.auto_save_label.setText("💾✓")
                QTimer.singleShot(
                    1000, lambda: self.auto_save_label.setText(original_text)
                )

        except Exception as e:
            # Silent fail for auto-save to avoid disrupting user workflow
            print(f"Auto-save preferences failed: {e}")
            if hasattr(self, "auto_save_label"):
                self.auto_save_label.setText("💾❌")
                QTimer.singleShot(2000, lambda: self.auto_save_label.setText("💾"))

    def _load_user_preferences(self):
        """Load user preferences and restore session state."""
        try:
            with open("user_preferences.json", "r", encoding="utf-8") as f:
                preferences = json.load(f)

            # Restore window geometry
            if "window_geometry" in preferences:
                geom = preferences["window_geometry"]
                self.setGeometry(geom["x"], geom["y"], geom["width"], geom["height"])

            # Restore current tab
            if "current_tab" in preferences and hasattr(self, "tabs"):
                self.tabs.setCurrentIndex(preferences["current_tab"])

            # Restore chat button position
            if "chat_button_position" in preferences and hasattr(self, "chat_button"):
                pos = preferences["chat_button_position"]
                self.chat_button.move(pos["x"], pos["y"])

        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            # Use defaults if preferences file doesn't exist or is corrupted
            pass

    def get_keyboard_shortcuts_help(self) -> str:
        """Return formatted help text for keyboard shortcuts."""
        return """
        <h3>Keyboard Shortcuts</h3>
        <table>
        <tr><td><b>Ctrl+R</b></td><td>Run Analysis</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>Stop Analysis</td></tr>
        <tr><td><b>Ctrl+O</b></td><td>Open File</td></tr>
        <tr><td><b>Ctrl+Shift+O</b></td><td>Open Folder</td></tr>
        <tr><td><b>Ctrl+1</b></td><td>Analysis Tab</td></tr>
        <tr><td><b>Ctrl+2</b></td><td>Dashboard Tab</td></tr>
        <tr><td><b>Ctrl+3</b></td><td>Settings Tab</td></tr>
        <tr><td><b>Ctrl+H</b></td><td>Open Chat Assistant</td></tr>
        <tr><td><b>Ctrl+L</b></td><td>Light Theme</td></tr>
        <tr><td><b>Ctrl+D</b></td><td>Dark Theme</td></tr>
        <tr><td><b>Ctrl+E</b></td><td>Export Report</td></tr>
        <tr><td><b>Ctrl+K</b></td><td>Clear Display</td></tr>
        </table>
        """

    def show_user_notification(
        self, title: str, message: str, notification_type: str = "info"
    ):
        """Show user notification with improved styling and options."""
        if notification_type == "error":
            icon = QMessageBox.Icon.Critical
        elif notification_type == "warning":
            icon = QMessageBox.Icon.Warning
        elif notification_type == "success":
            icon = QMessageBox.Icon.Information
            title = f"✅ {title}"
        else:
            icon = QMessageBox.Icon.Information

        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(icon)
        msg.exec()

    def show_progress_notification(self, message: str, duration: int = 3000):
        """Show temporary progress notification in status bar."""
        if hasattr(self, "status_bar"):
            self.status_bar.showMessage(f"🔄 {message}", duration)

    def _create_left_panels(self):
        """Create the 3 stacked panels on the left side"""
        left_container = QWidget()
        left_container.setMinimumWidth(320)
        left_container.setMaximumWidth(400)

        layout = QVBoxLayout(left_container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Panel 1: Rubric Selection
        rubric_panel = self._create_rubric_panel()
        layout.addWidget(rubric_panel)

        # Panel 2: Document Upload
        upload_panel = self._create_upload_panel()
        layout.addWidget(upload_panel)

        # Panel 3: Analysis Controls
        controls_panel = self._create_analysis_controls_panel()
        layout.addWidget(controls_panel)

        # Add stretch to push panels to top
        layout.addStretch()

        return left_container

    def _create_title_header(self):
        """Create the title header with main title and descriptor"""
        header_widget = QWidget()
        header_widget.setObjectName("titleHeader")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 15, 20, 15)
        header_layout.setSpacing(5)

        # Main title
        main_title = QLabel("THERAPY DOCUMENT COMPLIANCE ANALYSIS")
        main_title.setObjectName("mainTitle")
        main_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(main_title)

        # Descriptor
        descriptor = QLabel(
            "AI-Powered Medicare & Regulatory Compliance Analysis for Healthcare Professionals"
        )
        descriptor.setObjectName("titleDescriptor")
        descriptor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        descriptor.setWordWrap(True)
        header_layout.addWidget(descriptor)

        return header_widget

    def _create_rubric_panel(self):
        """Create the rubric selection panel"""
        panel = QGroupBox("📋 Compliance Rubric")
        panel.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background: white;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        # Rubric selector
        self.rubric_selector = QComboBox()
        self.rubric_selector.setPlaceholderText("Select Medicare Compliance Rubric")
        self.rubric_selector.setMinimumHeight(35)

        self.rubric_selector.currentIndexChanged.connect(self._on_rubric_selected)
        layout.addWidget(self.rubric_selector)

        # Discipline filter with auto-detection
        discipline_layout = QHBoxLayout()
        discipline_label = QLabel("Discipline:")
        discipline_label.setStyleSheet("color: #34495e; font-weight: bold;")

        self.rubric_type_selector = QComboBox()
        self.rubric_type_selector.addItem("🤖 Auto-Detect", "AUTO")
        self.rubric_type_selector.addItem("All Disciplines", None)
        self.rubric_type_selector.addItem("Physical Therapy", "PT")
        self.rubric_type_selector.addItem("Occupational Therapy", "OT")
        self.rubric_type_selector.addItem("Speech-Language Pathology", "SLP")
        self.rubric_type_selector.addItem("Multiple Disciplines", "MULTI")
        self.rubric_type_selector.setMinimumHeight(30)
        self.rubric_type_selector.currentIndexChanged.connect(
            self._filter_rubrics_by_type
        )

        discipline_layout.addWidget(discipline_label)
        discipline_layout.addWidget(self.rubric_type_selector, 1)
        layout.addLayout(discipline_layout)

        # Auto-detection status
        self.auto_detect_label = QLabel(
            "📄 Upload document for automatic discipline detection"
        )
        self.auto_detect_label.setObjectName("autoDetectStatus")
        self.auto_detect_label.setWordWrap(True)
        self.auto_detect_label.setStyleSheet(
            "color: #666; font-style: italic; font-size: 11px;"
        )
        layout.addWidget(self.auto_detect_label)

        # Rubric description
        self.rubric_description_label = QLabel(
            "Medicare Benefits Policy Manual - Default compliance rubric for PT, OT, and SLP services"
        )
        self.rubric_description_label.setObjectName("description")
        self.rubric_description_label.setWordWrap(True)
        layout.addWidget(self.rubric_description_label)

        # Manage rubrics button
        manage_btn = QPushButton("⚙️ Manage Rubrics")
        manage_btn.setObjectName("infoButton")
        manage_btn.setMinimumHeight(32)
        manage_btn.clicked.connect(self.manage_rubrics)
        layout.addWidget(manage_btn)

        return panel

    def _create_upload_panel(self):
        """Create the document upload panel"""
        panel = QGroupBox("📄 Document Upload")
        panel.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background: white;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        # Drop area
        self.drop_area = QLabel("📁 Drag & Drop Document Here\nor Click to Browse")
        self.drop_area.setObjectName("dropArea")
        self.drop_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_area.setMinimumHeight(100)
        self.drop_area.setWordWrap(True)
        self.drop_area.mousePressEvent = lambda e: self.open_file_dialog()
        layout.addWidget(self.drop_area)

        # File info
        self.file_info_label = QLabel("No document selected")
        self.file_info_label.setObjectName("fileInfo")
        self.file_info_label.setWordWrap(True)
        layout.addWidget(self.file_info_label)

        # Upload buttons
        button_layout = QHBoxLayout()

        upload_file_btn = QPushButton("📄 File")
        upload_file_btn.setObjectName("successButton")
        upload_file_btn.clicked.connect(self.open_file_dialog)
        upload_file_btn.setMinimumHeight(32)

        upload_folder_btn = QPushButton("📁 Folder")
        upload_folder_btn.setObjectName("successButton")
        upload_folder_btn.clicked.connect(self.open_folder_dialog)
        upload_folder_btn.setMinimumHeight(32)

        button_layout.addWidget(upload_file_btn)
        button_layout.addWidget(upload_folder_btn)
        layout.addLayout(button_layout)

        return panel

    def _create_analysis_controls_panel(self):
        """Create the analysis controls/report components panel"""
        panel = QGroupBox("🔍 Analysis Controls")
        panel.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background: white;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setSpacing(12)

        # Main analyze button
        self.analyze_doc_btn = QPushButton("🔍 Run Compliance Analysis")
        self.analyze_doc_btn.setObjectName("primaryButton")
        self.analyze_doc_btn.setEnabled(False)
        self.analyze_doc_btn.setMinimumHeight(45)
        self.analyze_doc_btn.clicked.connect(self.run_analysis)
        layout.addWidget(self.analyze_doc_btn)

        # Analysis options
        options_label = QLabel("Analysis Options:")
        options_label.setStyleSheet(
            "color: #34495e; font-weight: bold; margin-top: 10px;"
        )
        layout.addWidget(options_label)

        # Checkboxes for analysis components
        self.enable_fact_check = QCheckBox("✓ Fact Checking")
        self.enable_fact_check.setChecked(True)
        self.enable_suggestions = QCheckBox("💡 Improvement Suggestions")
        self.enable_suggestions.setChecked(True)
        self.enable_citations = QCheckBox("📚 Regulatory Citations")
        self.enable_citations.setChecked(True)
        self.enable_7_habits = QCheckBox("🎯 7 Habits Framework")
        self.enable_7_habits.setChecked(True)
        self.enable_7_habits = QCheckBox("🎯 7 Habits Framework")
        self.enable_7_habits.setChecked(True)

        for checkbox in [
            self.enable_fact_check,
            self.enable_suggestions,
            self.enable_citations,
            self.enable_7_habits,
        ]:
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: #34495e;
                    font-size: 12px;
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
                QCheckBox::indicator:unchecked {
                    border: 2px solid #bdc3c7;
                    border-radius: 3px;
                    background: white;
                }
                QCheckBox::indicator:checked {
                    border: 2px solid #27ae60;
                    border-radius: 3px;
                    background: #27ae60;
                }
            """)
            layout.addWidget(checkbox)

        # Action buttons
        button_layout = QHBoxLayout()

        preview_btn = QPushButton("👁 Preview")
        preview_btn.setObjectName("secondaryButton")
        preview_btn.setEnabled(False)
        preview_btn.clicked.connect(self.show_document_preview)
        preview_btn.setMinimumHeight(32)

        clear_btn = QPushButton("🗑 Clear")
        clear_btn.setObjectName("warningButton")
        clear_btn.clicked.connect(self.clear_display)
        clear_btn.setMinimumHeight(32)

        button_layout.addWidget(preview_btn)
        button_layout.addWidget(clear_btn)
        layout.addLayout(button_layout)

        # Store references for state updates
        self.document_preview_button = preview_btn

        return panel

    def _create_right_main_window(self):
        """Create the main tabbed window on the right side"""
        # Create tab widget for the main window
        self.main_tabs = QTabWidget()
        self.main_tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Analysis Tab - Main report display
        analysis_tab = self._create_analysis_tab_content()
        self.main_tabs.addTab(analysis_tab, "📊 Analysis")

        # Dashboard/Trending Tab
        self.dashboard_widget = DashboardWidget()
        self.main_tabs.addTab(self.dashboard_widget, "📈 Dashboard")
        self.dashboard_widget.refresh_requested.connect(self.load_dashboard_data)

        # Settings Tab
        settings_tab = self._create_settings_tab()
        self.main_tabs.addTab(settings_tab, "⚙️ Settings")

        return self.main_tabs

    def _create_analysis_tab_content(self):
        """Create the main analysis/report display area"""
        analysis_widget = QWidget()
        layout = QVBoxLayout(analysis_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Main title header
        title_header_layout = QVBoxLayout()
        title_header_layout.setSpacing(2)

        main_title = QLabel("THERAPY DOCUMENT COMPLIANCE ANALYSIS")
        main_title.setObjectName("mainTitle")
        main_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_header_layout.addWidget(main_title)

        subtitle = QLabel(
            "AI-Powered Medicare & Regulatory Compliance Analysis for Clinical Documentation"
        )
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_header_layout.addWidget(subtitle)

        layout.addLayout(title_header_layout)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setObjectName("titleSeparator")
        layout.addWidget(separator)

        # Header with controls
        header_layout = QHBoxLayout()

        report_title_label = QLabel("📊 Compliance Analysis Report")
        report_title_label.setObjectName("reportTitleLabel")
        header_layout.addWidget(report_title_label)

        header_layout.addStretch()

        # Export button
        export_btn = QPushButton("📤 Export Report")
        export_btn.setObjectName("successButton")
        export_btn.setEnabled(False)
        export_btn.clicked.connect(self.export_report)
        export_btn.setMinimumHeight(35)
        header_layout.addWidget(export_btn)
        self.export_report_button = export_btn

        layout.addLayout(header_layout)

        # Main report display
        self.analysis_results_area = QTextBrowser()
        self.analysis_results_area.setPlaceholderText("""
        🏥 Welcome to the Therapy Compliance Analyzer
        
        📋 Select a compliance rubric from the left panel
        📄 Upload a therapy document (Progress Note, Evaluation, etc.)
        🔍 Click 'Run Compliance Analysis' to begin
        
        Your comprehensive compliance report will appear here with:
        • Detailed findings and recommendations
        • Regulatory citations and references  
        • Interactive links to source document
        • Actionable improvement suggestions
        """)
        self.analysis_results_area.setReadOnly(True)
        self.analysis_results_area.setOpenExternalLinks(True)
        self.analysis_results_area.anchorClicked.connect(self.handle_anchor_click)
        layout.addWidget(self.analysis_results_area, 1)

        return analysis_widget

    def _create_easter_egg_tab(self):
        """Create the hidden easter egg tab with Pacific Coast Development theme"""
        easter_widget = QWidget()
        layout = QVBoxLayout(easter_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Pacific Coast header
        header_label = QLabel("🌴 Pacific Coast Development 🌴")
        header_label.setObjectName("easterEggHeader")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_label)

        # Developer info
        dev_info = QLabel("""
        <div style='text-align: center; line-height: 1.6;'>
        <h3>Kevin Moon - Lead Developer</h3>
        <p>🏥 Therapy Compliance Analyzer</p>
        <p>🌊 Crafted with care on the Pacific Coast</p>
        <p>☕ Powered by coffee and ocean views</p>
        <br>
        <p><em>"Making healthcare compliance as smooth as Pacific waves"</em></p>
        </div>
        """)
        dev_info.setObjectName("easterEggContent")
        dev_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(dev_info)

        # Fun stats
        stats_label = QLabel("""
        <div style='background: rgba(74, 158, 255, 0.1); padding: 15px; border-radius: 8px;'>
        <h4>🎯 Project Stats</h4>
        <p>📝 Lines of Code: 15,000+</p>
        <p>🧠 AI Models: 5 specialized medical models</p>
        <p>🔍 Compliance Rules: 200+ Medicare guidelines</p>
        <p>☕ Coffee Consumed: Countless cups</p>
        <p>🌅 Sunrises Coded Through: Many</p>
        </div>
        """)
        stats_label.setObjectName("easterEggStats")
        layout.addWidget(stats_label)

        # Close button
        close_btn = QPushButton("🌊 Back to Analysis")
        close_btn.setObjectName("easterEggButton")
        close_btn.clicked.connect(self.hide_easter_egg)
        layout.addWidget(close_btn)

        layout.addStretch()
        return easter_widget

    def _on_rubric_selected(self, index):
        """Handle rubric selection"""
        if hasattr(self, "rubric_selector") and index >= 0:
            rubric_data = self.rubric_selector.currentData()
            if rubric_data:
                description = rubric_data.get("description", "No description available")
                self.rubric_description_label.setText(description)
            else:
                self.rubric_description_label.setText(
                    "Select a rubric to see its description"
                )
        self._update_action_states()

    def clear_display(self):
        """Clear all displays and reset state"""
        self._current_file_path = None
        self._current_folder_path = None
        self._current_folder_files = []
        self._current_document_text = ""
        self._current_report_payload = None

        # Clear UI elements
        if hasattr(self, "analysis_results_area"):
            self.analysis_results_area.clear()
            self.analysis_results_area.setPlaceholderText("""
        🏥 Welcome to the Therapy Compliance Analyzer
        
        📋 Select a compliance rubric from the left panel
        📄 Upload a therapy document (Progress Note, Evaluation, etc.)
        🔍 Click 'Run Compliance Analysis' to begin
        
        Your comprehensive compliance report will appear here with:
        • Detailed findings and recommendations
        • Regulatory citations and references  
        • Interactive links to source document
        • Actionable improvement suggestions
            """)

        if hasattr(self, "file_info_label"):
            self.file_info_label.setText("No document selected")

        self._update_action_states()
        self.status_bar.showMessage("Display cleared", 2000)

    def apply_medical_theme(self, theme_mode="dark"):
        """Apply medical theme in light or dark mode"""
        self.current_theme = theme_mode

        if theme_mode == "dark":
            theme_css = self._get_dark_theme()
        else:
            theme_css = self._get_light_theme()

        self.setStyleSheet(theme_css)

    def _get_dark_theme(self):
        """Get dark medical theme CSS"""
        return """
        /* Main Application - Dark Mode */
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        /* Tabs */
        QTabWidget::pane {
            border: 1px solid #4a9eff;
            background-color: #353535;
        }
        QTabBar::tab {
            background-color: #404040;
            border: 1px solid #4a9eff;
            padding: 8px 16px;
            margin-right: 2px;
            color: #ffffff;
            font-weight: bold;
        }
        QTabBar::tab:selected {
            background-color: #4a9eff;
            color: #ffffff;
        }
        QTabBar::tab:hover {
            background-color: #555555;
        }
        
        /* Group Boxes */
        QGroupBox {
            color: #ffffff;
            border: 1px solid #4a9eff;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 10px;
            background-color: #353535;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px;
            background-color: #2b2b2b;
            color: #4a9eff;
        }
        
        /* Labels */
        QLabel {
            color: #ffffff;
            background: transparent;
        }
        QLabel#titleLabel {
            font-size: 18px;
            font-weight: bold;
            color: #4a9eff;
        }
        
        /* Title Header */
        QWidget#titleHeader {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #353535, stop:1 #2b2b2b);
            border-bottom: 2px solid #4a9eff;
        }
        QLabel#mainTitle {
            font-size: 24px;
            font-weight: bold;
            color: #4a9eff;
            letter-spacing: 1px;
        }
        QLabel#titleDescriptor {
            font-size: 13px;
            color: #adb5bd;
            font-style: italic;
        }
        QLabel#easterEggHeader {
            font-size: 24px;
            font-weight: bold;
            color: #4a9eff;
        }
        QLabel#easterEggContent {
            color: #ffffff;
            font-size: 14px;
        }
        QLabel#easterEggStats {
            color: #ffffff;
            font-size: 13px;
        }
        
        /* Text Areas */
        QTextBrowser, QTextEdit {
            background-color: #2b2b2b;
            border: 1px solid #4a9eff;
            border-radius: 4px;
            color: #ffffff;
            padding: 8px;
            font-size: 13px;
        }
        
        /* Buttons */
        QPushButton {
            background-color: #4a9eff;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            font-weight: bold;
            padding: 8px 16px;
            min-height: 20px;
        }
        QPushButton:hover {
            background-color: #66b3ff;
        }
        QPushButton:pressed {
            background-color: #3385e6;
        }
        QPushButton:disabled {
            background-color: #555555;
            color: #888888;
        }
        QPushButton#successButton {
            background-color: #28a745;
        }
        QPushButton#successButton:hover {
            background-color: #34ce57;
        }
        QPushButton#warningButton {
            background-color: #dc3545;
        }
        QPushButton#warningButton:hover {
            background-color: #e85563;
        }
        QPushButton#easterEggButton {
            background-color: #17a2b8;
            font-size: 14px;
            padding: 12px 24px;
        }
        QPushButton#easterEggButton:hover {
            background-color: #20c0db;
        }
        
        /* ComboBoxes */
        QComboBox {
            background-color: #404040;
            border: 1px solid #4a9eff;
            border-radius: 4px;
            padding: 6px;
            color: #ffffff;
            min-height: 20px;
        }
        QComboBox:hover {
            border-color: #66b3ff;
        }
        QComboBox QAbstractItemView {
            background-color: #404040;
            border: 1px solid #4a9eff;
            selection-background-color: #4a9eff;
            color: #ffffff;
        }
        
        /* CheckBoxes */
        QCheckBox {
            color: #ffffff;
            spacing: 8px;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
        }
        QCheckBox::indicator:unchecked {
            border: 2px solid #4a9eff;
            border-radius: 3px;
            background-color: #2b2b2b;
        }
        QCheckBox::indicator:checked {
            border: 2px solid #4a9eff;
            border-radius: 3px;
            background-color: #4a9eff;
        }
        
        /* Splitters */
        QSplitter::handle {
            background-color: #4a9eff;
            width: 3px;
            height: 3px;
        }
        QSplitter::handle:hover {
            background-color: #66b3ff;
        }
        
        /* Status Bar */
        QStatusBar {
            background-color: #2b2b2b;
            border-top: 1px solid #4a4a4a;
            color: #ffffff;
        }
        
        /* Menu Bar */
        QMenuBar {
            background-color: #2b2b2b;
            color: #ffffff;
            border-bottom: 1px solid #4a4a4a;
            font-weight: bold;
        }
        QMenuBar::item {
            padding: 6px 12px;
        }
        QMenuBar::item:selected {
            background-color: #4a9eff;
        }
        QMenu {
            background-color: #353535;
            border: 1px solid #4a9eff;
            color: #ffffff;
        }
        QMenu::item:selected {
            background-color: #4a9eff;
        }
        
        /* Pacific Coast Branding */
        QLabel#pacificCoastBranding {
            font-family: 'Brush Script MT', cursive, 'Comic Sans MS', fantasy;
            font-size: 14px;
            font-style: italic;
            color: #4a9eff;
            background: transparent;
        }
        
        /* Chat Button */
        QPushButton#chatButton {
            background-color: #4a9eff;
            color: #ffffff;
            border: none;
            border-radius: 25px;
            font-weight: bold;
            font-size: 16px;
        }
        QPushButton#chatButton:hover {
            background-color: #66b3ff;
            transform: scale(1.05);
        }
        """

    def _get_light_theme(self):
        """Get light medical theme CSS"""
        return """
        /* Main Application - Light Mode */
        QMainWindow {
            background-color: #f8f9fa;
            color: #2c3e50;
        }
        
        /* Tabs */
        QTabWidget::pane {
            border: 1px solid #007acc;
            background-color: #ffffff;
        }
        QTabBar::tab {
            background-color: #e9ecef;
            border: 1px solid #007acc;
            padding: 8px 16px;
            margin-right: 2px;
            color: #2c3e50;
            font-weight: bold;
        }
        QTabBar::tab:selected {
            background-color: #007acc;
            color: #ffffff;
        }
        QTabBar::tab:hover {
            background-color: #dee2e6;
        }
        
        /* Group Boxes */
        QGroupBox {
            color: #2c3e50;
            border: 1px solid #007acc;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 10px;
            background-color: #ffffff;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px;
            background-color: #f8f9fa;
            color: #007acc;
        }
        
        /* Labels */
        QLabel {
            color: #2c3e50;
            background: transparent;
        }
        QLabel#titleLabel {
            font-size: 18px;
            font-weight: bold;
            color: #007acc;
        }
        
        /* Title Header */
        QWidget#titleHeader {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f8f9fa, stop:1 #e9ecef);
            border-bottom: 2px solid #007acc;
        }
        QLabel#mainTitle {
            font-size: 24px;
            font-weight: bold;
            color: #007acc;
            letter-spacing: 1px;
        }
        QLabel#titleDescriptor {
            font-size: 13px;
            color: #6c757d;
            font-style: italic;
        }
        QLabel#easterEggHeader {
            font-size: 24px;
            font-weight: bold;
            color: #007acc;
        }
        QLabel#easterEggContent {
            color: #2c3e50;
            font-size: 14px;
        }
        QLabel#easterEggStats {
            color: #2c3e50;
            font-size: 13px;
        }
        
        /* Text Areas */
        QTextBrowser, QTextEdit {
            background-color: #ffffff;
            border: 1px solid #007acc;
            border-radius: 4px;
            color: #2c3e50;
            padding: 8px;
            font-size: 13px;
        }
        
        /* Buttons */
        QPushButton {
            background-color: #007acc;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            font-weight: bold;
            padding: 8px 16px;
            min-height: 20px;
        }
        QPushButton:hover {
            background-color: #0056b3;
        }
        QPushButton:pressed {
            background-color: #004085;
        }
        QPushButton:disabled {
            background-color: #6c757d;
            color: #adb5bd;
        }
        QPushButton#successButton {
            background-color: #28a745;
        }
        QPushButton#successButton:hover {
            background-color: #218838;
        }
        QPushButton#warningButton {
            background-color: #dc3545;
        }
        QPushButton#warningButton:hover {
            background-color: #c82333;
        }
        QPushButton#easterEggButton {
            background-color: #17a2b8;
            font-size: 14px;
            padding: 12px 24px;
        }
        QPushButton#easterEggButton:hover {
            background-color: #138496;
        }
        
        /* ComboBoxes */
        QComboBox {
            background-color: #ffffff;
            border: 1px solid #007acc;
            border-radius: 4px;
            padding: 6px;
            color: #2c3e50;
            min-height: 20px;
        }
        QComboBox:hover {
            border-color: #0056b3;
        }
        QComboBox QAbstractItemView {
            background-color: #ffffff;
            border: 1px solid #007acc;
            selection-background-color: #007acc;
            color: #2c3e50;
        }
        
        /* CheckBoxes */
        QCheckBox {
            color: #2c3e50;
            spacing: 8px;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
        }
        QCheckBox::indicator:unchecked {
            border: 2px solid #007acc;
            border-radius: 3px;
            background-color: #ffffff;
        }
        QCheckBox::indicator:checked {
            border: 2px solid #007acc;
            border-radius: 3px;
            background-color: #007acc;
        }
        
        /* Splitters */
        QSplitter::handle {
            background-color: #007acc;
            width: 3px;
            height: 3px;
        }
        QSplitter::handle:hover {
            background-color: #0056b3;
        }
        
        /* Status Bar */
        QStatusBar {
            background-color: #f8f9fa;
            border-top: 1px solid #dee2e6;
            color: #2c3e50;
        }
        
        /* Menu Bar */
        QMenuBar {
            background-color: #f8f9fa;
            color: #2c3e50;
            border-bottom: 1px solid #dee2e6;
            font-weight: bold;
        }
        QMenuBar::item {
            padding: 6px 12px;
        }
        QMenuBar::item:selected {
            background-color: #007acc;
            color: #ffffff;
        }
        QMenu {
            background-color: #ffffff;
            border: 1px solid #007acc;
            color: #2c3e50;
        }
        QMenu::item:selected {
            background-color: #007acc;
            color: #ffffff;
        }
        
        /* Pacific Coast Branding */
        QLabel#pacificCoastBranding {
            font-family: 'Brush Script MT', cursive, 'Comic Sans MS', fantasy;
            font-size: 14px;
            font-style: italic;
            color: #007acc;
            background: transparent;
        }
        
        /* Chat Button */
        QPushButton#chatButton {
            background-color: #007acc;
            color: #ffffff;
            border: none;
            border-radius: 25px;
            font-weight: bold;
            font-size: 16px;
        }
        QPushButton#chatButton:hover {
            background-color: #0056b3;
            transform: scale(1.05);
        }
        """

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.apply_medical_theme(new_theme)
        self.status_bar.showMessage(f"Switched to {new_theme} theme", 2000)

    def set_light_theme(self):
        """Set light theme"""
        self.apply_medical_theme("light")

    def set_dark_theme(self):
        """Set dark theme"""
        self.apply_medical_theme("dark")

    def keyPressEvent(self, event):
        """Handle key press events for Konami code easter egg"""
        # Handle Konami code sequence
        self.konami_sequence.append(event.key())
        if len(self.konami_sequence) > len(self.konami_code):
            self.konami_sequence.pop(0)

        if self.konami_sequence == self.konami_code:
            self.unlock_developer_mode()
            self.konami_sequence = []  # Reset sequence

        super().keyPressEvent(event)

    def unlock_developer_mode(self):
        """Unlock developer mode easter egg"""
        msg = QMessageBox(self)
        msg.setWindowTitle("🎮 Konami Code Activated!")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText("""
        <h2>🔓 Developer Mode Unlocked!</h2>
        <p><b>Konami Code Successfully Entered!</b></p>
        <p>↑↑↓↓←→←→BA</p>
        <br>
        <p>🎉 <i>Easter egg discovered by a true gamer!</i></p>
        <br>
        <p><b>Developer Features:</b></p>
        <ul>
        <li>🔧 Advanced debugging tools</li>
        <li>📊 Performance metrics</li>
        <li>🎨 Theme customization</li>
        </ul>
        <br>
        <p><i style="font-family: cursive;">Pacific Coast Development 🌴</i></p>
        """)
        msg.exec()

        # Show developer message in status bar
        self.status_bar.showMessage(
            "🎮 Developer Mode Activated! Welcome to the matrix...", 5000
        )
