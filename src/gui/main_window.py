
"""Primary GUI window for the Therapy Compliance Analyzer."""
from __future__ import annotations

import functools
import json
import webbrowser
import requests
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type, Protocol
from urllib.parse import urlparse, parse_qs

from PySide6.QtCore import Qt, QThread, QSettings, QObject, Signal, QUrl
from PySide6.QtGui import QAction, QFont, QIcon, QActionGroup
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QInputDialog,
)

from src.config import get_settings
from src.database import models
from src.core.report_generator import ReportGenerator
from src.gui.dialogs.chat_dialog import ChatDialog
from src.gui.dialogs.rubric_manager_dialog import RubricManagerDialog
from src.gui.dialogs.batch_analysis_dialog import BatchAnalysisDialog
from src.gui.dialogs.change_password_dialog import ChangePasswordDialog
from src.gui.dialogs.settings_dialog import SettingsDialog
from src.gui.workers.analysis_starter_worker import AnalysisStarterWorker
from src.gui.themes import get_theme_palette
from src.gui.workers.generic_api_worker import GenericApiWorker, HealthCheckWorker, TaskMonitorWorker, LogStreamWorker, FeedbackWorker
from src.gui.workers.single_analysis_polling_worker import SingleAnalysisPollingWorker

# Import beautiful medical-themed components
from src.gui.components.header_component import HeaderComponent
from src.gui.components.status_component import StatusComponent
from src.gui.widgets.medical_theme import medical_theme

from src.gui.widgets.mission_control_widget import MissionControlWidget, LogViewerWidget, SettingsEditorWidget
from src.gui.widgets.dashboard_widget import DashboardWidget

try:
    from src.gui.widgets.meta_analytics_widget import MetaAnalyticsWidget
except ImportError:
    MetaAnalyticsWidget = None

try:
    from src.gui.widgets.performance_status_widget import PerformanceStatusWidget
except ImportError:
    PerformanceStatusWidget = None

SETTINGS = get_settings()
API_URL = SETTINGS.paths.api_url


class WorkerProtocol(Protocol):
    def run(self) -> None: ...
    def moveToThread(self, thread: QThread) -> None: ...


class MainViewModel(QObject):
    """ViewModel for the MainApplicationWindow, handling state and business logic."""
    status_message_changed = Signal(str)
    api_status_changed = Signal(str, str)
    task_list_changed = Signal(dict)
    log_message_received = Signal(str)
    settings_loaded = Signal(dict)
    analysis_result_received = Signal(dict)
    rubrics_loaded = Signal(list)
    dashboard_data_loaded = Signal(dict)
    meta_analytics_loaded = Signal(dict)

    def __init__(self, auth_token: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.auth_token = auth_token
        self._active_threads: list[QThread] = []

    def start_workers(self) -> None:
        self._start_health_check_worker()
        self._start_task_monitor_worker()
        self._start_log_stream_worker()
        self.load_rubrics()
        self.load_dashboard_data()
        if MetaAnalyticsWidget:
            self.load_meta_analytics()

    def _run_worker(
        self,
        worker_class: Type[WorkerProtocol],
        on_success: Callable | None = None,
        on_error: Callable | None = None,
        *,
        success_signal: Optional[str] = "success",
        error_signal: Optional[str] = "error",
        auto_stop: bool = True,
        start_slot: str = "run",
        **kwargs: Any,
    ) -> None:
        thread = QThread()
        worker = worker_class(**kwargs)
        worker.moveToThread(thread)
        setattr(thread, "_worker_ref", worker)

        def connect_signal(signal_name: Optional[str], callback: Callable | None, should_quit: bool) -> None:
            if not signal_name:
                return
            if not hasattr(worker, signal_name):
                if callback is not None:
                    raise AttributeError(f"{worker_class.__name__} does not expose signal '{signal_name}'")
                return
            signal = getattr(worker, signal_name)
            if callback is not None:
                signal.connect(callback)
            if should_quit:
                signal.connect(thread.quit)

        connect_signal(success_signal, on_success, auto_stop)
        connect_signal(error_signal, on_error, auto_stop)

        if hasattr(worker, "finished"):
            getattr(worker, "finished").connect(thread.quit)

        thread.finished.connect(thread.deleteLater)
        if hasattr(worker, "deleteLater"):
            thread.finished.connect(worker.deleteLater)

        def _cleanup() -> None:
            if hasattr(thread, "_worker_ref"):
                setattr(thread, "_worker_ref", None)
            if thread in self._active_threads:
                self._active_threads.remove(thread)

        thread.finished.connect(_cleanup)

        start_callable = getattr(worker, start_slot)
        thread.started.connect(start_callable)

        self._active_threads.append(thread)
        thread.start()


    def _start_health_check_worker(self) -> None:
        self._run_worker(
            HealthCheckWorker,
            on_success=self.api_status_changed.emit,
            success_signal="status_update",
            error_signal=None,
            auto_stop=False,
        )

    def _start_task_monitor_worker(self) -> None:
        self._run_worker(
            TaskMonitorWorker,
            on_success=self.task_list_changed.emit,
            on_error=lambda msg: self.status_message_changed.emit(f"Task Monitor Error: {msg}"),
            success_signal="tasks_updated",
            auto_stop=False,
            token=self.auth_token,
        )

    def _start_log_stream_worker(self) -> None:
        self._run_worker(
            LogStreamWorker,
            on_success=self.log_message_received.emit,
            on_error=lambda msg: self.status_message_changed.emit(f"Log Stream: {msg}"),
            success_signal="new_log_message",
            auto_stop=False,
        )

    def load_rubrics(self) -> None:
        self._run_worker(GenericApiWorker, on_success=self.rubrics_loaded.emit, on_error=lambda msg: self.status_message_changed.emit(f"Could not load rubrics: {msg}"), endpoint="/rubrics", token=self.auth_token)

    def load_dashboard_data(self) -> None:
        self._run_worker(GenericApiWorker, on_success=self.dashboard_data_loaded.emit, on_error=lambda msg: self.status_message_changed.emit(f"Could not load dashboard data: {msg}"), endpoint="/dashboard/statistics", token=self.auth_token)

    def load_meta_analytics(self, params: Dict[str, Any] = None) -> None:
        endpoint = "/meta-analytics/widget_data"
        if params:
            param_str = f"days_back={params.get('days_back', 90)}&discipline={params.get('discipline', '')}"
            endpoint += f"?{param_str}"
        self._run_worker(GenericApiWorker, on_success=self.meta_analytics_loaded.emit, on_error=lambda msg: self.status_message_changed.emit(f"Could not load meta-analytics: {msg}"), endpoint=endpoint, token=self.auth_token)

    def start_analysis(self, file_path: str, options: dict) -> None:
        self.status_message_changed.emit(f"Submitting document for analysis: {Path(file_path).name}")
        self._run_worker(AnalysisStarterWorker, on_success=self._handle_analysis_task_started, on_error=lambda msg: self.status_message_changed.emit(f"Analysis failed: {msg}"), file_path=file_path, data=options, token=self.auth_token)

    def _handle_analysis_task_started(self, task_id: str) -> None:
        self.status_message_changed.emit("Analysis running…")
        self._run_worker(SingleAnalysisPollingWorker, on_success=self.analysis_result_received.emit, on_error=lambda msg: self.status_message_changed.emit(f"Polling failed: {msg}"), task_id=task_id, token=self.auth_token)

    def load_settings(self) -> None:
        self._run_worker(GenericApiWorker, on_success=self.settings_loaded.emit, on_error=lambda msg: self.status_message_changed.emit(f"Failed to load settings: {msg}"), endpoint="/admin/settings", token=self.auth_token)

    def save_settings(self, settings: dict) -> None:
        class SettingsSaveWorker(QThread):
            success = Signal(str)
            error = Signal(str)
            def run(self_worker) -> None:
                try:
                    response = requests.post(f"{API_URL}/admin/settings", headers={"Authorization": f"Bearer {self.auth_token}"}, json=settings, timeout=10)
                    response.raise_for_status()
                    self_worker.success.emit(response.json().get("message", "Success!"))
                except Exception as e:
                    self_worker.error.emit(str(e))
        self._run_worker(SettingsSaveWorker, on_success=lambda msg: self.status_message_changed.emit(msg), on_error=lambda msg: self.status_message_changed.emit(f"Failed to save settings: {msg}"))

    def submit_feedback(self, feedback_data: Dict[str, Any]) -> None:
        self._run_worker(FeedbackWorker, on_success=self.status_message_changed.emit, on_error=lambda msg: self.status_message_changed.emit(f"Feedback Error: {msg}"), token=self.auth_token, feedback_data=feedback_data)

    def stop_all_workers(self) -> None:
        for thread in list(self._active_threads):
            worker = getattr(thread, "_worker_ref", None)
            if worker and hasattr(worker, "stop"):
                try:
                    worker.stop()
                except Exception:
                    pass
            try:
                if thread.isRunning():
                    thread.quit()
                    thread.wait()
            except RuntimeError:
                continue


class MainApplicationWindow(QMainWindow):
    """The main application window (View)."""

    def __init__(self, user: models.User, token: str) -> None:
        super().__init__()
        self.setWindowTitle(f"Therapy Compliance Analyzer - Welcome, {user.username}!")
        self.resize(1440, 920)

        self.current_user = user
        self.settings = QSettings("TherapyCo", "ComplianceAnalyzer")
        self.report_generator = ReportGenerator()
        self._current_payload: Dict[str, Any] = {}
        self._selected_file: Optional[Path] = None
        self._cached_preview_content: str = ""

        self.view_model = MainViewModel(token)
        self.mission_control_widget = MissionControlWidget(self)

        self._build_ui()
        self._connect_view_model()
        self._load_initial_state()
        self._load_gui_settings()

    def _build_ui(self) -> None:
        self._build_header()
        self._build_docks()
        self._build_menus()
        self._build_central_layout()
        self._build_status_bar()
        self._build_floating_chat_button()
        self._setup_keyboard_shortcuts()
        self._apply_medical_theme()

    def _build_header(self) -> None:
        """Build the beautiful medical-themed header with 🏥 emoji and theme toggle."""
        # Create header component
        self.header = HeaderComponent(self)
        self.header.theme_toggle_requested.connect(self._toggle_theme)
        self.header.logo_clicked.connect(self._on_logo_clicked)
        
        # Create status component for AI models
        self.status_component = StatusComponent(self)
        self.status_component.status_clicked.connect(self._on_model_status_clicked)
        
        # Apply header stylesheet
        self.header.setStyleSheet(self.header.get_default_stylesheet())
        
        # Note: Header will be added to central layout in _build_central_layout

    def _apply_medical_theme(self) -> None:
        """Apply the comprehensive medical theme styling."""
        # Apply main window stylesheet
        self.setStyleSheet(medical_theme.get_main_window_stylesheet())
        
        # Update header theme
        is_dark = medical_theme.current_theme == "dark"
        self.header.update_theme_button(is_dark)
        if is_dark:
            self.header.setStyleSheet(self.header.get_dark_theme_stylesheet())
        else:
            self.header.setStyleSheet(self.header.get_default_stylesheet())

    def _toggle_theme(self) -> None:
        """Toggle between light and dark theme."""
        medical_theme.toggle_theme()
        self._apply_medical_theme()
        
        # Update status bar message
        theme_name = "Dark" if medical_theme.current_theme == "dark" else "Light"
        self.statusBar().showMessage(f"Switched to {theme_name} theme", 3000)

    def _on_logo_clicked(self) -> None:
        """Handle logo clicks for easter eggs (7 clicks triggers special message)."""
        if self.header.click_count == 7:
            QMessageBox.information(
                self,
                "🎉 Easter Egg Found!",
                "You found the secret! 🌴\n\n"
                "Pacific Coast Therapy - Where compliance meets excellence!\n\n"
                "Keep up the great documentation work! 💪"
            )
            self.statusBar().showMessage("🎉 Easter egg activated!", 5000)

    def _on_model_status_clicked(self, model_name: str) -> None:
        """Handle clicks on AI model status indicators."""
        status = self.status_component.models.get(model_name, False)
        status_text = "Ready" if status else "Not Ready"
        QMessageBox.information(
            self,
            f"AI Model Status: {model_name}",
            f"Model: {model_name}\nStatus: {status_text}\n\n"
            f"This model is used for compliance analysis and documentation review."
        )

    def _connect_view_model(self) -> None:
        self.view_model.status_message_changed.connect(self.statusBar().showMessage)
        self.view_model.api_status_changed.connect(self.mission_control_widget.update_api_status)
        self.view_model.task_list_changed.connect(self.mission_control_widget.update_task_list)
        self.view_model.log_message_received.connect(self.log_viewer.add_log_message)
        self.view_model.settings_loaded.connect(self.settings_editor.set_settings)
        self.view_model.analysis_result_received.connect(self._handle_analysis_success)
        self.view_model.rubrics_loaded.connect(self._on_rubrics_loaded)
        self.view_model.dashboard_data_loaded.connect(self.dashboard_widget.load_data)
        if MetaAnalyticsWidget:
            self.view_model.meta_analytics_loaded.connect(self.meta_widget.update_data)

    def _load_initial_state(self) -> None:
        self.view_model.start_workers()
        if self.current_user.is_admin:
            self.view_model.load_settings()

    def _start_analysis(self) -> None:
        if not self._selected_file:
            QMessageBox.warning(self, "No document", "Please select a document before starting the analysis.")
            return
        
        options = {
            "discipline": self.rubric_selector.currentData() or "",
            "analysis_mode": "rubric",
        }
        self.run_analysis_button.setEnabled(False)
        self.view_model.start_analysis(str(self._selected_file), options)

    def _handle_analysis_success(self, payload: Dict[str, Any]) -> None:
        self.statusBar().showMessage("Analysis complete", 5000)
        self.run_analysis_button.setEnabled(True)
        self._current_payload = payload
        analysis = payload.get("analysis", {})
        doc_name = self._selected_file.name if self._selected_file else "Document"
        report_html = payload.get("report_html") or self.report_generator.generate_html_report(analysis_result=analysis, doc_name=doc_name)
        self.analysis_summary_browser.setHtml(report_html)
        self.report_preview_browser.setHtml(report_html)
        self.detailed_results_browser.setPlainText(json.dumps(payload, indent=2))
        self.view_model.load_dashboard_data() # Refresh dashboard after analysis

        if self.auto_analysis_queue_list.count() > 0:
            self._process_auto_analysis_queue()

    def on_analysis_error(self, message: str) -> None:
        """Handles analysis errors by re-enabling controls and surfacing the status."""
        self.statusBar().showMessage(f"Analysis failed: {message}", 5000)
        self.run_analysis_button.setEnabled(True)

    def _on_rubrics_loaded(self, rubrics: list[dict]) -> None:
        """Load rubrics into dropdown with default rubrics always available."""
        self.rubric_selector.clear()
        
        # Add default rubrics first
        self.rubric_selector.addItem("📋 Medicare Policy Manual (Default)", "medicare_policy_manual")
        self.rubric_selector.addItem("📋 Part B Guidelines (Default)", "part_b_guidelines")
        
        # Add separator if there are custom rubrics
        if rubrics:
            self.rubric_selector.insertSeparator(2)
        
        # Add custom rubrics from API
        for rubric in rubrics:
            self.rubric_selector.addItem(rubric.get("name", "Unnamed rubric"), rubric.get("value"))
        
        # Select first default rubric
        self.rubric_selector.setCurrentIndex(0)
        
        self._load_gui_settings() # Re-apply settings after rubrics are loaded

    def _handle_link_clicked(self, url: QUrl) -> None:
        if url.scheme() == "feedback":
            parsed_url = urlparse(url.toString())
            query_params = parse_qs(parsed_url.query)
            finding_id = query_params.get("finding_id", [None])[0]
            action = parsed_url.path.strip("/")

            if not finding_id:
                return

            if action == "correct":
                self.view_model.submit_feedback({"finding_id": finding_id, "is_correct": True})
                self.statusBar().showMessage(f"Feedback for finding {finding_id[:8]}... marked as correct.", 3000)
            elif action == "incorrect":
                correction, ok = QInputDialog.getText(self, "Submit Correction", "Please provide a brief correction:")
                if ok and correction:
                    self.view_model.submit_feedback({"finding_id": finding_id, "is_correct": False, "correction": correction})
                    self.statusBar().showMessage(f"Correction for finding {finding_id[:8]}... submitted.", 3000)
        else:
            webbrowser.open(url.toString())

    def closeEvent(self, event) -> None:
        self._save_gui_settings()
        self.view_model.stop_all_workers()
        super().closeEvent(event)

    def _build_menus(self) -> None:
        menu_bar = self.menuBar()
        self._build_file_menu(menu_bar)
        self._build_view_menu(menu_bar)
        self._build_tools_menu(menu_bar)
        self._build_admin_menu(menu_bar)
        self._build_help_menu(menu_bar)

    def _build_file_menu(self, menu_bar: QMenu) -> None:
        file_menu = menu_bar.addMenu("&File")
        open_file_action = QAction("Open Document…", self)
        open_file_action.triggered.connect(self._prompt_for_document)
        file_menu.addAction(open_file_action)
        open_folder_action = QAction("Open Folder…", self)
        open_folder_action.triggered.connect(self._prompt_for_folder)
        file_menu.addAction(open_folder_action)
        file_menu.addSeparator()
        export_action = QAction("Export Report…", self)
        export_action.triggered.connect(self._export_report)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _build_view_menu(self, menu_bar: QMenu) -> None:
        view_menu = menu_bar.addMenu("&View")
        view_menu.addAction(self.document_preview_dock.toggleViewAction())
        view_menu.addAction(self.auto_analysis_dock.toggleViewAction())
        if self.performance_dock:
            view_menu.addAction(self.performance_dock.toggleViewAction())
        
        theme_menu = QMenu("Theme", self)
        self.theme_action_group = QActionGroup(self)
        self.theme_action_group.setExclusive(True)
        for name in ("light", "dark"):
            action = QAction(name.capitalize(), self, checkable=True)
            action.triggered.connect(functools.partial(self._apply_theme, name))
            theme_menu.addAction(action)
            self.theme_action_group.addAction(action)
        view_menu.addMenu(theme_menu)
    def _build_tools_menu(self, menu_bar: QMenu) -> None:
        tools_menu = menu_bar.addMenu("&Tools")
        
        # Meta Analytics
        if MetaAnalyticsWidget:
            meta_action = QAction("Meta Analytics", self, checkable=True)
            meta_action.setShortcut("Ctrl+Shift+A")
            meta_action.triggered.connect(self._toggle_meta_analytics_dock)
            tools_menu.addAction(meta_action)
            self.meta_analytics_action = meta_action
        
        # Performance Status
        if PerformanceStatusWidget:
            perf_action = QAction("Performance Status", self, checkable=True)
            perf_action.setShortcut("Ctrl+Shift+P")
            perf_action.triggered.connect(self._toggle_performance_dock)
            tools_menu.addAction(perf_action)
            self.performance_action = perf_action
        
        tools_menu.addSeparator()
        
        # Refresh
        refresh_action = QAction("Refresh All Data", self)
        refresh_action.triggered.connect(self._load_initial_state)
        tools_menu.addAction(refresh_action)

    def _build_admin_menu(self, menu_bar: QMenu) -> None:
        if not self.current_user.is_admin:
            return
        admin_menu = menu_bar.addMenu("&Admin")
        rubrics_action = QAction("Manage Rubrics…", self)
        rubrics_action.triggered.connect(self._open_rubric_manager)
        admin_menu.addAction(rubrics_action)
        admin_menu.addSeparator()
        settings_action = QAction("Settings…", self)
        settings_action.triggered.connect(self._open_settings_dialog)
        admin_menu.addAction(settings_action)

    def _build_help_menu(self, menu_bar: QMenu) -> None:
        help_menu = menu_bar.addMenu("&Help")
        docs_action = QAction("Open Documentation", self)
        docs_action.triggered.connect(lambda: webbrowser.open("https://github.com/your-username/your-repo-name"))
        help_menu.addAction(docs_action)
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _build_central_layout(self) -> None:
        """Build the main central widget with 4-tab structure."""
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)
        
        # Create main tab widget with 4 tabs
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setDocumentMode(True)
        root_layout.addWidget(self.tab_widget, stretch=1)
        
        # Tab 1: Analysis (with left 3 panels + right chat/analysis)
        self.analysis_tab = self._create_analysis_tab()
        self.tab_widget.addTab(self.analysis_tab, "Analysis")
        
        # Tab 2: Dashboard
        self.dashboard_tab = self._create_dashboard_tab()
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        
        # Tab 3: Mission Control
        self.mission_control_tab = self._create_mission_control_tab()
        self.tab_widget.addTab(self.mission_control_tab, "Mission Control")
        
        # Tab 4: Settings
        self.settings_tab = self._create_settings_tab()
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
        # Set Analysis as default tab
        self.tab_widget.setCurrentWidget(self.analysis_tab)

    def _create_analysis_tab(self) -> QWidget:
        """Create the Analysis tab with left (3 panels) and right (chat/analysis) layout."""
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main horizontal splitter
        main_splitter = QSplitter(Qt.Horizontal, tab)
        main_splitter.setChildrenCollapsible(False)
        
        # Left panel with 3 vertical sections
        left_panel = self._create_analysis_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Right panel with chat/analysis
        right_panel = self._create_analysis_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Set stretch factors (30% left, 70% right)
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 7)
        
        layout.addWidget(main_splitter)
        return tab
    
    def _create_analysis_left_panel(self) -> QWidget:
        """Create the left panel with 3 vertical sections: Rubric, Report Preview, Report Outputs."""
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Vertical splitter for 3 sections
        left_splitter = QSplitter(Qt.Vertical, panel)
        left_splitter.setChildrenCollapsible(False)
        
        # Top: Rubric Selection Panel
        rubric_panel = self._create_rubric_selection_panel()
        left_splitter.addWidget(rubric_panel)
        
        # Middle: Report Preview Panel
        report_preview_panel = self._create_report_preview_panel()
        left_splitter.addWidget(report_preview_panel)
        
        # Bottom: Report Outputs Panel
        report_outputs_panel = self._create_report_outputs_panel()
        left_splitter.addWidget(report_outputs_panel)
        
        # Set initial sizes (30%, 40%, 30%)
        left_splitter.setStretchFactor(0, 3)
        left_splitter.setStretchFactor(1, 4)
        left_splitter.setStretchFactor(2, 3)
        
        layout.addWidget(left_splitter)
        return panel
    
    def _create_rubric_selection_panel(self) -> QWidget:
        """Create the Rubric selection panel (top left)."""
        panel = QWidget(self)
        panel.setMinimumWidth(280)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("Select Rubric", panel)
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)
        
        # File selection
        layout.addWidget(self._create_file_selection_group(panel))
        
        # Rubric selector
        rubric_label = QLabel("Compliance Rubric:", panel)
        layout.addWidget(rubric_label)
        self.rubric_selector = QComboBox(panel)
        layout.addWidget(self.rubric_selector)
        
        # Run Analysis button
        self.run_analysis_button = QPushButton("Run Analysis", panel)
        self.run_analysis_button.setIcon(QIcon.fromTheme("media-playback-start"))
        self.run_analysis_button.clicked.connect(self._start_analysis)
        self.run_analysis_button.setEnabled(False)
        layout.addWidget(self.run_analysis_button)
        
        layout.addStretch(1)
        return panel
    
    def _create_report_preview_panel(self) -> QWidget:
        """Create the Report preview panel (middle left)."""
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("Report Preview", panel)
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Report browser
        self.report_preview_browser = QTextBrowser(panel)
        self.report_preview_browser.setOpenExternalLinks(False)
        self.report_preview_browser.anchorClicked.connect(self._handle_link_clicked)
        layout.addWidget(self.report_preview_browser)
        
        return panel
    
    def _create_report_outputs_panel(self) -> QWidget:
        """Create the Report outputs panel (bottom left)."""
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("Report Outputs", panel)
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Outputs list
        self.report_outputs_list = QListWidget(panel)
        layout.addWidget(self.report_outputs_list)
        
        # Export button
        export_button = QPushButton("Export Selected", panel)
        export_button.clicked.connect(self._export_report)
        layout.addWidget(export_button)
        
        return panel
    
    def _create_analysis_right_panel(self) -> QWidget:
        """Create the right panel with Chat/Analysis tabs."""
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Tab widget for Chat and Analysis
        right_tabs = QTabWidget(panel)
        
        # Analysis results tab
        analysis_widget = QWidget()
        analysis_layout = QVBoxLayout(analysis_widget)
        analysis_layout.setContentsMargins(0, 0, 0, 0)
        self.analysis_summary_browser = QTextBrowser(analysis_widget)
        self.analysis_summary_browser.setOpenExternalLinks(False)
        self.analysis_summary_browser.anchorClicked.connect(self._handle_link_clicked)
        analysis_layout.addWidget(self.analysis_summary_browser)
        right_tabs.addTab(analysis_widget, "Analysis Results")
        
        # Detailed findings tab
        detailed_widget = QWidget()
        detailed_layout = QVBoxLayout(detailed_widget)
        detailed_layout.setContentsMargins(0, 0, 0, 0)
        self.detailed_results_browser = QTextBrowser(detailed_widget)
        detailed_layout.addWidget(self.detailed_results_browser)
        right_tabs.addTab(detailed_widget, "Detailed Findings")
        
        # Chat tab (placeholder for now)
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_label = QLabel("AI Chat Assistant\n\nClick the 'Ask AI Assistant' button to open the chat dialog.", chat_widget)
        chat_label.setAlignment(Qt.AlignCenter)
        chat_layout.addWidget(chat_label)
        right_tabs.addTab(chat_widget, "Chat")
        
        layout.addWidget(right_tabs)
        return panel

    def _create_file_selection_group(self, parent: QWidget) -> QWidget:
        group = QWidget(parent)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.file_display = QTextEdit(group)
        self.file_display.setReadOnly(True)
        self.file_display.setMaximumHeight(80)
        self.file_display.setPlaceholderText("No document selected")
        layout.addWidget(self.file_display)
        controls_row = QHBoxLayout()
        self.open_file_button = QPushButton("Browse…", group)
        self.open_file_button.clicked.connect(self._prompt_for_document)
        controls_row.addWidget(self.open_file_button)
        self.open_folder_button = QPushButton("Folder…", group)
        self.open_folder_button.clicked.connect(self._prompt_for_folder)
        controls_row.addWidget(self.open_folder_button)
        layout.addLayout(controls_row)
        return group

    def _create_mission_control_tab(self) -> QWidget:
        """Create the Mission Control tab."""
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.mission_control_widget = MissionControlWidget(tab)
        self.mission_control_widget.start_analysis_requested.connect(self._handle_mission_control_start)
        self.mission_control_widget.review_document_requested.connect(self._handle_mission_control_review)
        layout.addWidget(self.mission_control_widget)
        return tab



    def _handle_mission_control_start(self) -> None:
        """Handle start analysis request from Mission Control."""
        self.tab_widget.setCurrentWidget(self.analysis_tab)
        self._prompt_for_document()

    def _handle_mission_control_review(self, doc_info: dict) -> None:
        """Handle review document request from Mission Control."""
        doc_name = doc_info.get("title") or doc_info.get("name") or doc_info.get("document_name") or "Document"
        self.statusBar().showMessage(f"Detailed replay for '{doc_name}' will be available in a future update.")
    
    def _toggle_meta_analytics_dock(self) -> None:
        """Toggle Meta Analytics dock widget visibility."""
        if self.meta_analytics_dock:
            if self.meta_analytics_dock.isVisible():
                self.meta_analytics_dock.hide()
            else:
                self.meta_analytics_dock.show()
                self.view_model.load_meta_analytics()
    
    def _toggle_performance_dock(self) -> None:
        """Toggle Performance Status dock widget visibility."""
        if self.performance_dock:
            if self.performance_dock.isVisible():
                self.performance_dock.hide()
            else:
                self.performance_dock.show()
    
    def _open_change_password_dialog(self) -> None:
        """Open the change password dialog."""
        dialog = ChangePasswordDialog(self.current_user, self)
        dialog.exec()
    
    def _setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts for tab navigation."""
        # Ctrl+1: Analysis tab
        shortcut_analysis = QAction(self)
        shortcut_analysis.setShortcut("Ctrl+1")
        shortcut_analysis.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        self.addAction(shortcut_analysis)
        
        # Ctrl+2: Dashboard tab
        shortcut_dashboard = QAction(self)
        shortcut_dashboard.setShortcut("Ctrl+2")
        shortcut_dashboard.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        self.addAction(shortcut_dashboard)
        
        # Ctrl+3: Mission Control tab
        shortcut_mission = QAction(self)
        shortcut_mission.setShortcut("Ctrl+3")
        shortcut_mission.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        self.addAction(shortcut_mission)
        
        # Ctrl+4: Settings tab
        shortcut_settings = QAction(self)
        shortcut_settings.setShortcut("Ctrl+4")
        shortcut_settings.triggered.connect(lambda: self.tab_widget.setCurrentIndex(3))
        self.addAction(shortcut_settings)



    def _create_dashboard_tab(self) -> QWidget:
        """Create the Dashboard tab."""
        tab, layout = self._create_tab_base_layout()
        self.dashboard_widget = DashboardWidget() if DashboardWidget else QTextBrowser()
        if not DashboardWidget:
            self.dashboard_widget.setPlainText("Dashboard component unavailable.")
        else:
            self.dashboard_widget.refresh_requested.connect(self.view_model.load_dashboard_data)
        layout.addWidget(self.dashboard_widget)
        return tab
    
    def _create_settings_tab(self) -> QWidget:
        """Create the Settings tab."""
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("Application Settings", tab)
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Settings tabs
        settings_tabs = QTabWidget(tab)
        
        # User Preferences
        user_prefs_widget = self._create_user_preferences_widget()
        settings_tabs.addTab(user_prefs_widget, "User Preferences")
        
        # Performance Settings
        perf_widget = self._create_performance_settings_widget()
        settings_tabs.addTab(perf_widget, "Performance")
        
        # Analysis Settings
        analysis_settings_widget = self._create_analysis_settings_widget()
        settings_tabs.addTab(analysis_settings_widget, "Analysis")
        
        # Admin Settings (if admin)
        if self.current_user.is_admin:
            self.settings_editor = SettingsEditorWidget(tab)
            self.settings_editor.save_requested.connect(self.view_model.save_settings)
            settings_tabs.addTab(self.settings_editor, "Advanced (Admin)")
        
        layout.addWidget(settings_tabs)
        return tab
    
    def _create_user_preferences_widget(self) -> QWidget:
        """Create user preferences settings widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Theme selection
        theme_label = QLabel("Theme:", widget)
        layout.addWidget(theme_label)
        
        theme_group = QWidget()
        theme_layout = QHBoxLayout(theme_group)
        light_button = QPushButton("Light", theme_group)
        light_button.clicked.connect(lambda: self._apply_theme("light"))
        theme_layout.addWidget(light_button)
        dark_button = QPushButton("Dark", theme_group)
        dark_button.clicked.connect(lambda: self._apply_theme("dark"))
        theme_layout.addWidget(dark_button)
        theme_layout.addStretch()
        layout.addWidget(theme_group)
        
        # Password change
        password_button = QPushButton("Change Password", widget)
        password_button.clicked.connect(self._open_change_password_dialog)
        layout.addWidget(password_button)
        
        layout.addStretch()
        return widget
    
    def _create_performance_settings_widget(self) -> QWidget:
        """Create performance settings widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        info_label = QLabel("Performance settings will be available in a future update.", widget)
        layout.addWidget(info_label)
        
        layout.addStretch()
        return widget
    
    def _create_analysis_settings_widget(self) -> QWidget:
        """Create analysis settings widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        info_label = QLabel("Analysis settings will be available in a future update.", widget)
        layout.addWidget(info_label)
        
        layout.addStretch()
        return widget



    def _create_tab_base_layout(self, spacing: int = 0) -> tuple[QWidget, QVBoxLayout]:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(spacing)
        return tab, layout

    def _create_browser_tab(self, parent: Optional[QWidget] = None) -> tuple[QTextBrowser, QWidget]:
        tab, layout = self._create_tab_base_layout()
        browser = QTextBrowser(tab)
        layout.addWidget(browser)
        return browser, tab

    def _build_status_bar(self) -> None:
        """Build status bar with progress indicator and branding."""
        status: QStatusBar = self.statusBar()
        status.showMessage("Ready")
        
        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximumWidth(180)
        self.progress_bar.hide()
        status.addPermanentWidget(self.progress_bar)
        
        # Pacific Coast Therapy branding in bottom right
        branding_label = QLabel("🌴 Pacific Coast Therapy")
        branding_label.setObjectName("brandingLabel")
        branding_label.setStyleSheet("""
            QLabel#brandingLabel {
                font-family: "Brush Script MT", "Lucida Handwriting", "Comic Sans MS", cursive;
                font-size: 11px;
                color: #94a3b8;
                font-style: italic;
                padding-right: 10px;
            }
        """)
        branding_label.setToolTip("Powered by Pacific Coast Therapy")
        status.addPermanentWidget(branding_label)

    def _build_docks(self) -> None:
        """Build dock widgets for document preview, auto-analysis, meta analytics, and performance."""
        # Document Preview Dock
        self.document_preview_dock = QDockWidget("Document Preview", self)
        self.document_preview_dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.document_preview_browser = QTextBrowser(self.document_preview_dock)
        self.document_display_area = self.document_preview_browser
        self.document_preview_dock.setWidget(self.document_preview_browser)
        self.addDockWidget(Qt.RightDockWidgetArea, self.document_preview_dock)

        # Auto-Analysis Queue Dock
        self._build_auto_analysis_dock()
        
        # Meta Analytics Dock (hidden by default, accessible via Tools menu)
        if MetaAnalyticsWidget:
            self.meta_analytics_dock = QDockWidget("Meta Analytics", self)
            self.meta_analytics_dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)
            self.meta_widget = MetaAnalyticsWidget()
            self.meta_widget.refresh_requested.connect(self.view_model.load_meta_analytics)
            self.meta_analytics_dock.setWidget(self.meta_widget)
            self.addDockWidget(Qt.BottomDockWidgetArea, self.meta_analytics_dock)
            self.meta_analytics_dock.hide()  # Hidden by default
        else:
            self.meta_analytics_dock = None
        
        # Performance Status Dock (hidden by default, accessible via Tools menu)
        if PerformanceStatusWidget:
            self.performance_dock = QDockWidget("Performance Status", self)
            self.performance_dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
            self.performance_widget = PerformanceStatusWidget()
            self.performance_dock.setWidget(self.performance_widget)
            self.addDockWidget(Qt.RightDockWidgetArea, self.performance_dock)
            self.performance_dock.hide()  # Hidden by default
        else:
            self.performance_dock = None
        
        # Log Viewer (create widget for Mission Control to use)
        self.log_viewer = LogViewerWidget(self)

    def _build_auto_analysis_dock(self) -> None:
        self.auto_analysis_dock = QDockWidget("Auto-Analysis Queue", self)
        self.auto_analysis_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        self.auto_analysis_queue_list = QListWidget()
        layout.addWidget(self.auto_analysis_queue_list)

        button_layout = QHBoxLayout()
        add_files_button = QPushButton("Add Files…")
        add_files_button.clicked.connect(self._add_files_to_auto_analysis_queue)
        button_layout.addWidget(add_files_button)

        process_button = QPushButton("Process Queue")
        process_button.clicked.connect(self._process_auto_analysis_queue)
        button_layout.addWidget(process_button)
        layout.addLayout(button_layout)
        
        self.auto_analysis_dock.setWidget(container)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.auto_analysis_dock)

    def _add_files_to_auto_analysis_queue(self) -> None:
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select documents to queue for analysis", str(Path.home()), "Documents (*.pdf *.docx *.txt *.md *.json)")
        if file_paths:
            for path in file_paths:
                item = QListWidgetItem(path)
                self.auto_analysis_queue_list.addItem(item)
            self.statusBar().showMessage(f"Added {len(file_paths)} files to the queue.")

    def _process_auto_analysis_queue(self) -> None:
        count = self.auto_analysis_queue_list.count()
        if count == 0:
            QMessageBox.information(self, "Queue Empty", "There are no files in the queue to process.")
            return

        self.statusBar().showMessage(f"Starting to process {count} files from the queue…")
        
        item = self.auto_analysis_queue_list.takeItem(0)
        if item:
            file_path = item.text()
            self._selected_file = Path(file_path)
            self._start_analysis()

    def _build_floating_chat_button(self) -> None:
        """Create floating AI chat button in bottom left corner."""
        self.chat_button = QPushButton("💬 Ask AI Assistant", self)
        self.chat_button.setObjectName("floatingChatButton")
        self.chat_button.clicked.connect(self._open_chat_dialog)
        self.chat_button.setStyleSheet("""
            QPushButton#floatingChatButton {
                background-color: #4a90e2;
                color: white;
                border-radius: 22px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
                border: none;
            }
            QPushButton#floatingChatButton:hover {
                background-color: #357abd;
                transform: scale(1.05);
            }
            QPushButton#floatingChatButton:pressed {
                background-color: #2968a3;
            }
        """)
        self.chat_button.resize(200, 44)
        self.chat_button.raise_()

    def _apply_theme(self, theme: str) -> None:
        QApplication.instance().setPalette(get_theme_palette(theme))
        for action in self.theme_action_group.actions():
            if action.text().lower() == theme:
                action.setChecked(True)

    def _save_gui_settings(self) -> None:
        """Save GUI settings including window geometry, theme, and preferences."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("ui/last_active_tab", self.tab_widget.currentIndex())
        
        if self.theme_action_group.checkedAction():
            self.settings.setValue("theme", self.theme_action_group.checkedAction().text().lower())
        self.settings.setValue("analysis/rubric", self.rubric_selector.currentData())
        if self._selected_file:
            self.settings.setValue("analysis/last_file", str(self._selected_file))
        
        # Save dock widget states
        if self.meta_analytics_dock:
            self.settings.setValue("docks/meta_analytics_visible", self.meta_analytics_dock.isVisible())
        if self.performance_dock:
            self.settings.setValue("docks/performance_status_visible", self.performance_dock.isVisible())

    def _load_gui_settings(self) -> None:
        """Load GUI settings including window geometry, theme, and preferences."""
        if geometry := self.settings.value("geometry"):
            self.restoreGeometry(geometry)
        if window_state := self.settings.value("windowState"):
            self.restoreState(window_state)
        
        # Restore last active tab
        last_tab = self.settings.value("ui/last_active_tab", 0, type=int)
        if 0 <= last_tab < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(last_tab)
        
        saved_theme = self.settings.value("theme", "light", type=str)
        self._apply_theme(saved_theme)

        if saved_rubric_data := self.settings.value("analysis/rubric"):
            index = self.rubric_selector.findData(saved_rubric_data)
            if index >= 0:
                self.rubric_selector.setCurrentIndex(index)

        if last_file_str := self.settings.value("analysis/last_file", type=str):
            last_file = Path(last_file_str)
            if last_file.exists():
                self._set_selected_file(last_file)
        
        # Restore dock widget visibility
        if self.meta_analytics_dock:
            visible = self.settings.value("docks/meta_analytics_visible", False, type=bool)
            if visible:
                self.meta_analytics_dock.show()
            if hasattr(self, 'meta_analytics_action'):
                self.meta_analytics_action.setChecked(visible)
        
        if self.performance_dock:
            visible = self.settings.value("docks/performance_status_visible", False, type=bool)
            if visible:
                self.performance_dock.show()
            if hasattr(self, 'performance_action'):
                self.performance_action.setChecked(visible)

    def open_file_dialog(self) -> None:
        """Public wrapper to trigger the standard file picker."""
        self._prompt_for_document()

    def _prompt_for_document(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Select clinical document", str(Path.home()), "Documents (*.pdf *.docx *.txt *.md *.json)")
        if file_path:
            self._set_selected_file(Path(file_path))

    def _set_selected_file(self, file_path: Path) -> None:
        self.run_analysis_button.setEnabled(False)
        self._cached_preview_content = ""
        try:
            max_preview_chars = 2_000_000
            with open(file_path, "r", encoding="utf-8", errors="ignore") as stream:
                content = stream.read(max_preview_chars)
        except FileNotFoundError:
            self.statusBar().showMessage(f"File not found: {file_path.name}", 5000)
            placeholder = f"Preview unavailable: {file_path.name} not found."
            self._selected_file = file_path
            self._cached_preview_content = placeholder
            self.file_display.setPlainText(placeholder)
            self.document_display_area.setPlainText(placeholder)
            self.run_analysis_button.setEnabled(True)
            return
        except Exception as exc:
            self._selected_file = None
            error_message = f"Could not display preview: {exc}"
            self.file_display.setPlainText(error_message)
            self.document_display_area.setPlainText(error_message)
            self.statusBar().showMessage(f"Failed to load {file_path.name}", 5000)
            return

        self._selected_file = file_path
        self._cached_preview_content = content
        self.file_display.setPlainText(content[:4000])
        self.document_display_area.setPlainText(content)
        self.statusBar().showMessage(f"Selected {self._selected_file.name}", 3000)
        self.run_analysis_button.setEnabled(True)
        self._update_document_preview()

    def _update_document_preview(self) -> None:
        if self._cached_preview_content:
            self.document_display_area.setPlainText(self._cached_preview_content)
            return

        if self._selected_file and self._selected_file.exists():
            try:
                max_preview_chars = 2_000_000
                with open(self._selected_file, "r", encoding="utf-8", errors="ignore") as stream:
                    content = stream.read(max_preview_chars)
            except Exception as exc:
                self.document_display_area.setPlainText(f"Could not display preview: {exc}")
                self.run_analysis_button.setEnabled(False)
                return
            self._cached_preview_content = content
            self.document_display_area.setPlainText(content)
        else:
            self.document_display_area.clear()

    def _prompt_for_folder(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(self, "Select folder for batch analysis", str(Path.home()))
        if folder_path:
            analysis_data = {
                "discipline": self.rubric_selector.currentData() or "",
                "analysis_mode": "rubric",
            }
            dialog = BatchAnalysisDialog(folder_path, self.auth_token, analysis_data, self)
            dialog.exec()

    def _export_report(self) -> None:
        if not self._current_payload:
            QMessageBox.information(self, "No report", "Run an analysis before exporting a report.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save report",
            str(Path.home() / "compliance_report.html"),
            "HTML Files (*.html)",
        )
        if not file_path:
            return

        Path(file_path).write_text(self.report_preview_browser.toHtml(), encoding='utf-8')
        self.statusBar().showMessage(f"Report exported to {file_path}", 5000)

    def _open_rubric_manager(self) -> None:
        dialog = RubricManagerDialog(self.auth_token, self)
        if dialog.exec():
            self.view_model.load_rubrics()

    def _open_settings_dialog(self) -> None:
        dialog = SettingsDialog(self)
        dialog.exec()

    def show_change_password_dialog(self) -> None:
        """Opens the change password dialog."""
        dialog = ChangePasswordDialog(self)
        dialog.exec()

    def _open_chat_dialog(self) -> None:
        initial_context = self.analysis_summary_browser.toPlainText() or "Provide a compliance summary."
        dialog = ChatDialog(initial_context, self.auth_token, self)
        dialog.exec()

    def _show_about_dialog(self) -> None:
        QMessageBox.information(self, "About", f"Therapy Compliance Analyzer\nWelcome, {self.current_user.username}!")

    def resizeEvent(self, event) -> None:
        """Handle window resize to reposition floating chat button."""
        super().resizeEvent(event)
        margin = 24
        button_width = self.chat_button.width()
        button_height = self.chat_button.height()
        # Position in BOTTOM LEFT corner
        self.chat_button.move(margin, self.height() - button_height - margin)

__all__ = ["MainApplicationWindow"]


