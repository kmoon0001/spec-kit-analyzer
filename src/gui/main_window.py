import os
import json
import requests
import urllib.parse
import webbrowser
from typing import Dict
from PyQt6.QtCore import Qt, QThread, QUrl
from PyQt6.QtGui import QTextDocument
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QDialog,
    QMessageBox,
    QMainWindow,
    QStatusBar,
    QMenuBar,
    QMenu,
    QFileDialog,
    QSplitter,
    QTextEdit,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QProgressBar,
    QToolButton,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QComboBox,
)

from src.config import get_settings
from src.gui.dialogs.rubric_manager_dialog import RubricManagerDialog
from src.gui.dialogs.change_password_dialog import ChangePasswordDialog
from src.gui.dialogs.chat_dialog import ChatDialog
from src.gui.workers.analysis_starter_worker import AnalysisStarterWorker

from src.gui.workers.folder_analysis_starter_worker import FolderAnalysisStarterWorker
from src.gui.workers.folder_analysis_worker import FolderAnalysisWorker
from src.gui.workers.single_analysis_polling_worker import SingleAnalysisPollingWorker
from src.gui.workers.ai_loader_worker import AILoaderWorker
from src.gui.workers.dashboard_worker import DashboardWorker
from src.gui.workers.meta_analytics_worker import MetaAnalyticsWorker
from src.gui.widgets.dashboard_widget import DashboardWidget
from src.gui.widgets.meta_analytics_widget import MetaAnalyticsWidget
from src.gui.widgets.performance_status_widget import PerformanceStatusWidget
from src.gui.dialogs.performance_settings_dialog import PerformanceSettingsDialog
from src.core.report_generator import ReportGenerator
from src.gui.export import generate_pdf_report

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
        self.access_token = None
        self.username = None
        self.is_admin = False
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
        self.model_status = {
            "Generator": False,
            "Retriever": False,
            "Fact Checker": False,
            "NER": False,
            "Checklist": False,
            "Chat": False,
        }
        self.init_base_ui()

    def start(self):
        """
        Starts the application's main logic, including loading models and showing the login dialog.
        This is called after the window is created to avoid blocking the constructor,
        which makes the main window testable.
        """
        self.load_ai_models()
        self.load_main_ui()  # Load main UI directly
        self.show()

    def init_base_ui(self):
        self.setWindowTitle("Therapy Compliance Analyzer")
        self.setGeometry(100, 100, 1200, 800)
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        self.file_menu = self.menu_bar.addMenu("File")
        self.file_menu.addAction("Logout", self.logout)
        self.file_menu.addSeparator()
        self.file_menu.addAction("Exit", self.close)
        self.tools_menu = self.menu_bar.addMenu("Tools")
        self.tools_menu.addAction("Manage Rubrics", self.manage_rubrics)
        self.tools_menu.addAction(
            "Performance Settings", self.show_performance_settings
        )
        self.tools_menu.addAction("Change Password", self.show_change_password_dialog)
        self.theme_menu = self.menu_bar.addMenu("Theme")
        self.theme_menu.addAction("Light", self.set_light_theme)
        self.theme_menu.addAction("Dark", self.set_dark_theme)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        self.ai_status_label = QLabel("Loading AI models...")
        self.status_bar.addPermanentWidget(self.ai_status_label)
        self.user_status_label = QLabel("")
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

        self.progress_bar = QProgressBar(self.status_bar)
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()

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

    def logout(self):
        self.access_token = None
        self.username = None
        self.is_admin = False
        self.user_status_label.setText("")
        self.setCentralWidget(None)
        QMessageBox.information(self, "Logged Out", "You have been logged out.")
        # Since login is removed, we can just close or show a message.
        # For now, let's just clear the UI. A real implementation might close the app.

    def load_main_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        analysis_tab = self._create_analysis_tab()
        self.tabs.addTab(analysis_tab, "Analysis")
        self.dashboard_widget = DashboardWidget()
        self.tabs.addTab(self.dashboard_widget, "Dashboard")
        self.dashboard_widget.refresh_requested.connect(self.load_dashboard_data)
        
        # Add meta analytics tab for admin users
        if self.is_admin:
            self.meta_analytics_widget = MetaAnalyticsWidget()
            self.tabs.addTab(self.meta_analytics_widget, "Team Analytics")
            self.meta_analytics_widget.refresh_requested.connect(self.load_meta_analytics_data)
        
        if self.is_admin:
            self.admin_menu = self.menu_bar.addMenu("Admin")
            self.admin_menu.addAction("Open Admin Dashboard", self.open_admin_dashboard)
        self.load_dashboard_data()
        
        # Load meta analytics for admin users
        if self.is_admin:
            self.load_meta_analytics_data()
        
        theme = self.load_theme_setting()
        self.apply_stylesheet(theme)

    def open_admin_dashboard(self):
        webbrowser.open(f"{API_URL}/admin/dashboard?token={self.access_token}")

    def _create_analysis_tab(self) -> QWidget:
        analysis_widget = QWidget()
        main_layout = QVBoxLayout(analysis_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        controls_group = QGroupBox("Analysis Setup")
        controls_group_layout = QVBoxLayout()
        controls_group_layout.setContentsMargins(10, 8, 10, 8)
        controls_group_layout.setSpacing(6)
        controls_group.setLayout(controls_group_layout)
        main_layout.addWidget(controls_group)

        source_layout = QHBoxLayout()
        source_layout.setSpacing(8)
        self.upload_button = QToolButton()
        self.upload_button.setText("Upload Source")
        self.upload_button.setFixedHeight(34)
        self.upload_button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.upload_button.clicked.connect(self.open_file_dialog)
        self.upload_button_menu = QMenu(self.upload_button)
        file_action = self.upload_button_menu.addAction("Upload Document")
        if file_action:
            file_action.triggered.connect(self.open_file_dialog)
        folder_action = self.upload_button_menu.addAction("Upload Folder")
        if folder_action:
            folder_action.triggered.connect(self.open_folder_dialog)
        self.upload_button.setMenu(self.upload_button_menu)
        source_layout.addWidget(self.upload_button)

        self.selected_source_label = QLabel("No document selected.")
        self.selected_source_label.setObjectName("selectedSourceLabel")
        self.selected_source_label.setMinimumWidth(240)
        source_layout.addWidget(self.selected_source_label, 1)
        controls_group_layout.addLayout(source_layout)

        rubric_layout = QHBoxLayout()
        rubric_layout.setSpacing(8)
        rubric_layout.addWidget(QLabel("Rubric"))
        self.rubric_selector = QComboBox()
        self.rubric_selector.setPlaceholderText("Select a Rubric")
        self.rubric_selector.currentIndexChanged.connect(self._on_rubric_selected)
        rubric_layout.addWidget(self.rubric_selector, 1)
        self.rubric_type_selector = QComboBox()
        self.rubric_type_selector.addItem("All Disciplines", None)
        self.rubric_type_selector.currentIndexChanged.connect(
            self._filter_rubrics_by_type
        )
        rubric_layout.addWidget(self.rubric_type_selector)
        controls_group_layout.addLayout(rubric_layout)

        self.rubric_description_label = QLabel(
            "Description of selected rubric will appear here."
        )
        self.rubric_description_label.setWordWrap(True)
        controls_group_layout.addWidget(self.rubric_description_label)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(10)
        splitter.setObjectName("analysisSplitter")
        main_layout.addWidget(splitter, 1)

        document_group = QGroupBox("Document")
        document_group.setObjectName("documentPane")
        document_layout = QVBoxLayout()
        document_group.setLayout(document_layout)
        self.document_display_area = QTextEdit()
        self.document_display_area.setPlaceholderText(
            "Upload a document to see its content here."
        )
        self.document_display_area.setReadOnly(True)
        document_layout.addWidget(self.document_display_area)
        splitter.addWidget(document_group)

        results_group = QGroupBox("Analysis Results")
        results_group.setObjectName("resultsPane")
        results_layout = QVBoxLayout()
        results_group.setLayout(results_layout)
        self.analysis_results_area = QTextBrowser()
        self.analysis_results_area.setPlaceholderText(
            "Analysis results will appear here."
        )
        self.analysis_results_area.setReadOnly(True)
        self.analysis_results_area.setOpenExternalLinks(True)
        self.analysis_results_area.anchorClicked.connect(self.handle_anchor_click)
        results_layout.addWidget(self.analysis_results_area)
        splitter.addWidget(results_group)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("analysisProgress")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)
        self.run_analysis_button = QPushButton("Run Analysis")
        self.run_analysis_button.setEnabled(False)
        self.run_analysis_button.setFixedHeight(34)
        self.run_analysis_button.clicked.connect(self.run_analysis)
        actions_layout.addWidget(self.run_analysis_button)

        self.stop_analysis_button = QPushButton("Stop Analysis")
        self.stop_analysis_button.setEnabled(False)
        self.stop_analysis_button.setFixedHeight(34)
        self.stop_analysis_button.clicked.connect(self.stop_analysis)
        actions_layout.addWidget(self.stop_analysis_button)

        self.document_preview_button = QPushButton("Document Preview")
        self.document_preview_button.setEnabled(False)
        self.document_preview_button.setFixedHeight(34)
        self.document_preview_button.clicked.connect(self.show_document_preview)
        actions_layout.addWidget(self.document_preview_button)

        self.analytics_button = QPushButton("Analytics")
        self.analytics_button.setFixedHeight(34)
        self.analytics_button.clicked.connect(self.open_analytics_dashboard)
        actions_layout.addWidget(self.analytics_button)

        self.export_report_button = QPushButton("Export Report")
        self.export_report_button.setEnabled(False)
        self.export_report_button.setFixedHeight(34)
        self.export_report_button.clicked.connect(self.export_report)
        actions_layout.addWidget(self.export_report_button)

        self.clear_button = QPushButton("Clear Display")
        self.clear_button.setFixedHeight(34)
        self.clear_button.clicked.connect(self.clear_display)
        actions_layout.addWidget(self.clear_button)

        actions_layout.addStretch()
        main_layout.addLayout(actions_layout)

        self._update_action_states()
        return analysis_widget

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
        if hasattr(self, "run_analysis_button"):
            self.run_analysis_button.setEnabled(can_run)
        if hasattr(self, "stop_analysis_button"):
            self.stop_analysis_button.setEnabled(self._analysis_running)
        if hasattr(self, "document_preview_button"):
            self.document_preview_button.setEnabled(has_preview)
        if hasattr(self, "export_report_button"):
            self.export_report_button.setEnabled(has_report)
        if hasattr(self, "clear_button"):
            self.clear_button.setEnabled(has_source or has_preview or has_report)

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
        dialog = ChangePasswordDialog(self)
        if dialog.exec():
            current_password, new_password = dialog.get_passwords()
            try:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                payload = {
                    "current_password": current_password,
                    "new_password": new_password,
                }
                response = requests.post(
                    f"{API_URL}/auth/users/change-password",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                QMessageBox.information(
                    self, "Success", "Password changed successfully."
                )
            except requests.exceptions.RequestException as e:
                detail = (
                    e.response.json().get("detail", str(e)) if e.response else str(e)
                )
                QMessageBox.critical(
                    self, "Error", f"Failed to change password: {detail}"
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
        if not self.access_token:
            self.status_bar.showMessage("Login required to load analytics.", 5000)
            return

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
        if not self.access_token:
            self.status_bar.showMessage("Login required to load team analytics.", 5000)
            return

        if not self.is_admin:
            self.status_bar.showMessage("Admin access required for team analytics.", 5000)
            return

        self.status_bar.showMessage("Loading team analytics...")
        
        # Stop any existing meta analytics worker
        if hasattr(self, 'meta_analytics_thread') and self.meta_analytics_thread and self.meta_analytics_thread.isRunning():
            self.meta_analytics_thread.requestInterruption()
            self.meta_analytics_thread.quit()
            self.meta_analytics_thread.wait(2000)

        # Create new worker thread
        self.meta_analytics_thread = QThread()
        self.meta_analytics_worker = MetaAnalyticsWorker(
            base_url=f"http://localhost:{self.api_port}",
            token=self.access_token
        )
        
        # Set parameters if provided
        if params:
            self.meta_analytics_worker.set_parameters(
                days_back=params.get("days_back", 90),
                discipline=params.get("discipline"),
                load_type="overview"
            )
        
        self.meta_analytics_worker.moveToThread(self.meta_analytics_thread)
        
        # Connect signals
        self.meta_analytics_thread.started.connect(self.meta_analytics_worker.run)
        self.meta_analytics_worker.data_loaded.connect(self.on_meta_analytics_data_loaded)
        self.meta_analytics_worker.error_occurred.connect(
            lambda msg: self.status_bar.showMessage(f"Team Analytics Error: {msg}", 5000)
        )
        self.meta_analytics_worker.progress_updated.connect(
            lambda msg: self.status_bar.showMessage(msg, 2000)
        )
        self.meta_analytics_worker.finished.connect(self.meta_analytics_thread.quit)
        self.meta_analytics_thread.finished.connect(self.meta_analytics_worker.deleteLater)
        self.meta_analytics_thread.finished.connect(self._clear_meta_analytics_worker)
        
        self.meta_analytics_thread.start()

    def _clear_meta_analytics_worker(self):
        """Clean up meta analytics worker references."""
        self.meta_analytics_worker = None
        self.meta_analytics_thread = None

    def on_meta_analytics_data_loaded(self, data):
        """Handle loaded meta analytics data."""
        if hasattr(self, 'meta_analytics_widget'):
            self.meta_analytics_widget.update_data(data)
            self.status_bar.showMessage("Team analytics updated.", 3000)

    def run_analysis(self):
        if self._analysis_running:
            return

        source_path = self._current_file_path or self._current_folder_path
        if not source_path:
            QMessageBox.warning(
                self,
                "No Source Selected",
                "Please upload a document or folder before running analysis.",
            )
            return

        selected_rubric = self.rubric_selector.currentData()
        if not selected_rubric:
            QMessageBox.warning(
                self,
                "No Rubric Selected",
                "Please select a rubric before running analysis.",
            )
            return

        discipline = selected_rubric.get("discipline", "Unknown")
        rubric_id = selected_rubric.get("id")

        self.status_bar.showMessage("Optimizing performance...")
        try:
            from src.core.performance_integration import optimize_for_analysis

            optimization_results = optimize_for_analysis()
            if optimization_results.get("recommendations"):
                recommendations = "\n".join(optimization_results["recommendations"])
                QMessageBox.information(
                    self,
                    "Performance Recommendations",
                    f"Performance optimization completed:\n\n{recommendations}",
                )
        except Exception as exc:
            print(f"Performance optimization failed: {exc}")

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

    def clear_display(self):
        self.document_display_area.clear()
        self.analysis_results_area.clear()
        self._current_file_path = None
        self._current_folder_path = None
        self._current_folder_files = []
        self._current_document_text = ""
        self._current_report_payload = None
        self.selected_source_label.setText("No document selected.")
        self.status_bar.showMessage("Display cleared.")
        self._analysis_running = False
        self._update_action_states()

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

        payload_str = json.dumps(self._current_report_payload)
        success, message = generate_pdf_report(payload_str, parent=self)
        if success:
            QMessageBox.information(
                self,
                "Export Complete",
                f"Report saved to:\n{message}",
            )
        else:
            QMessageBox.warning(self, "Export Failed", message)

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

    def set_light_theme(self) -> None:
        self.apply_stylesheet("light")
        self.save_theme_setting("light")

    def set_dark_theme(self) -> None:
        self.apply_stylesheet("dark")
        self.save_theme_setting("dark")

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
