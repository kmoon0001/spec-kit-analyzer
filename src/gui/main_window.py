"""Primary GUI window for the Therapy Compliance Analyzer."""
from __future__ import annotations

import functools
import json
import webbrowser
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type, Protocol

from PySide6.QtCore import Qt, QThread, QTimer, QSettings, QObject, Signal
from PySide6.QtGui import QAction, QFont, QIcon, QActionGroup
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QFrame,
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
)

from src.config import get_settings
from src.database import models
from src.core.report_generator import ReportGenerator
from src.gui.dialogs.chat_dialog import ChatDialog
from src.gui.dialogs.rubric_manager_dialog import RubricManagerDialog
from src.gui.dialogs.batch_analysis_dialog import BatchAnalysisDialog
from src.gui.dialogs.settings_dialog import SettingsDialog
from src.gui.workers.analysis_starter_worker import AnalysisStarterWorker
from src.gui.themes import get_theme_palette
from src.gui.workers.generic_api_worker import GenericApiWorker, HealthCheckWorker, TaskMonitorWorker, LogStreamWorker
from src.gui.workers.single_analysis_polling_worker import SingleAnalysisPollingWorker
from src.gui.workers.folder_watcher_worker import FolderWatcherWorker

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
    success: Any
    error: Any
    finished: Any
    progress: Any
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

    def __init__(self, auth_token: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.auth_token = auth_token
        self._active_threads: list[QThread] = []

    def start_workers(self) -> None:
        self._start_health_check_worker()
        self._start_task_monitor_worker()
        self._start_log_stream_worker()
        self.load_rubrics()

    def _run_worker(self, worker_class: Type[WorkerProtocol], on_success: Callable, on_error: Callable, **kwargs: Any) -> None:
        thread = QThread()
        worker = worker_class(**kwargs)
        worker.moveToThread(thread)

        worker.success.connect(on_success)
        worker.error.connect(on_error)
        worker.finished.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        thread.started.connect(worker.run)
        
        self._active_threads.append(thread)
        thread.start()

    def _start_health_check_worker(self) -> None:
        self._run_worker(HealthCheckWorker, on_success=self.api_status_changed.emit, on_error=lambda msg: self.status_message_changed.emit(f"Health Check Error: {msg}"))

    def _start_task_monitor_worker(self) -> None:
        self._run_worker(TaskMonitorWorker, on_success=self.task_list_changed.emit, on_error=lambda msg: self.status_message_changed.emit(f"Task Monitor Error: {msg}"), token=self.auth_token)

    def _start_log_stream_worker(self) -> None:
        self._run_worker(LogStreamWorker, on_success=self.log_message_received.emit, on_error=lambda msg: self.status_message_changed.emit(f"Log Stream: {msg}"))

    def load_rubrics(self) -> None:
        self._run_worker(GenericApiWorker, on_success=self.rubrics_loaded.emit, on_error=lambda msg: self.status_message_changed.emit(f"Could not load rubrics: {msg}"), endpoint="/rubrics", token=self.auth_token)

    def start_analysis(self, file_path: str, options: dict) -> None:
        self.status_message_changed.emit("Submitting document for analysis…")
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

    def stop_all_workers(self) -> None:
        for thread in self._active_threads:
            thread.quit()
            thread.wait()


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

        self.view_model = MainViewModel(token)

        self._build_ui()
        self._connect_view_model()
        self._load_initial_state()

    def _build_ui(self) -> None:
        # ... (UI building methods remain largely the same)
        self._build_menus()
        self._build_central_layout()
        self._build_status_bar()
        self._build_docks()
        self._build_floating_chat_button()

    def _connect_view_model(self) -> None:
        self.view_model.status_message_changed.connect(self.statusBar().showMessage)
        self.view_model.api_status_changed.connect(self.mission_control_widget.update_api_status)
        self.view_model.task_list_changed.connect(self.mission_control_widget.update_task_list)
        self.view_model.log_message_received.connect(self.log_viewer.add_log_message)
        self.view_model.settings_loaded.connect(self.settings_editor.set_settings)
        self.view_model.analysis_result_received.connect(self._handle_analysis_success)
        self.view_model.rubrics_loaded.connect(self._on_rubrics_loaded)

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
        self.view_model.start_analysis(str(self._selected_file), options)

    def _handle_analysis_success(self, payload: Dict[str, Any]) -> None:
        self.statusBar().showMessage("Analysis complete", 5000)
        self._current_payload = payload
        analysis = payload.get("analysis", {})
        doc_name = self._selected_file.name if self._selected_file else "Document"
        report_html = payload.get("report_html") or self.report_generator.generate_html_report(analysis_result=analysis, doc_name=doc_name)
        self.analysis_summary_browser.setHtml(report_html)
        self.report_preview_browser.setHtml(report_html)
        self.detailed_results_browser.setPlainText(json.dumps(payload, indent=2))

    def _on_rubrics_loaded(self, rubrics: list[dict]) -> None:
        self.rubric_selector.clear()
        for rubric in rubrics:
            self.rubric_selector.addItem(rubric.get("name", "Unnamed rubric"), rubric.get("value"))

    def closeEvent(self, event) -> None:
        self.view_model.stop_all_workers()
        super().closeEvent(event)

    # ... (Other UI-only methods like _build_menus, _prompt_for_document, etc. remain)
    # Note: Methods that previously started workers now delegate to the ViewModel.

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
        toggle_preview_action = QAction("Toggle Document Preview", self, checkable=True)
        toggle_preview_action.setChecked(True)
        toggle_preview_action.triggered.connect(self._toggle_document_preview)
        view_menu.addAction(toggle_preview_action)
        if PerformanceStatusWidget:
            toggle_performance_action = QAction("Toggle Performance Panel", self, checkable=True)
            toggle_performance_action.setChecked(True)
            toggle_performance_action.triggered.connect(self._toggle_performance_panel)
            view_menu.addAction(toggle_performance_action)
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
        refresh_dashboards_action = QAction("Refresh Dashboards", self)
        refresh_dashboards_action.triggered.connect(self.view_model.load_initial_data) # Changed
        tools_menu.addAction(refresh_dashboards_action)

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
        docs_action.triggered.connect(lambda: webbrowser.open("https://github.com/"))
        help_menu.addAction(docs_action)
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _build_central_layout(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)
        self.main_splitter = QSplitter(Qt.Horizontal, self)
        self.main_splitter.setChildrenCollapsible(False)
        root_layout.addWidget(self.main_splitter, stretch=1)
        self.control_panel = self._create_control_panel()
        self.main_splitter.addWidget(self.control_panel)
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setDocumentMode(True)
        self.main_splitter.addWidget(self.tab_widget)
        self.mission_control_tab = self._create_mission_control_tab()
        self.tab_widget.addTab(self.mission_control_tab, "Mission Control")
        self.analysis_summary_tab = self._create_analysis_summary_tab()
        self.tab_widget.addTab(self.analysis_summary_tab, "Analysis Summary")
        self.detailed_results_tab = self._create_detailed_results_tab()
        self.tab_widget.addTab(self.detailed_results_tab, "Detailed Findings")
        self.dashboard_tab = self._create_dashboard_tab()
        self.tab_widget.addTab(self.dashboard_tab, "Dashboards")
        self.meta_tab = self._create_meta_tab()
        self.tab_widget.addTab(self.meta_tab, "Meta Analytics")
        self.report_tab = self._create_report_tab()
        self.tab_widget.addTab(self.report_tab, "Reports")
        self.log_stream_tab = self._create_log_stream_tab()
        self.tab_widget.addTab(self.log_stream_tab, "Log Stream")
        if self.current_user.is_admin:
            self.admin_tab = self._create_admin_tab()
            self.tab_widget.addTab(self.admin_tab, "Admin")
        self.tab_widget.setCurrentWidget(self.mission_control_tab)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)

    def _create_control_panel(self) -> QWidget:
        panel = QWidget(self)
        panel.setMinimumWidth(320)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        title = QLabel("Analysis Controls", panel)
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)
        layout.addWidget(self._create_file_selection_group(panel))
        self.rubric_selector = QComboBox(panel)
        layout.addWidget(self.rubric_selector)
        self.quick_actions_list = QListWidget(panel)
        self.quick_actions_list.setMaximumHeight(140)
        for label in ["Pre-check medical necessity", "Verify plan of care", "Audit SOAP structure"]:
            item = QListWidgetItem(label)
            item.setCheckState(Qt.Unchecked)
            self.quick_actions_list.addItem(item)
        layout.addWidget(self.quick_actions_list)
        self.analysis_button = QPushButton("Start Analysis", panel)
        self.analysis_button.setIcon(QIcon.fromTheme("media-playback-start"))
        self.analysis_button.clicked.connect(self._start_analysis)
        layout.addWidget(self.analysis_button)
        layout.addStretch(1)
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
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.mission_control_widget = MissionControlWidget(tab)
        self.mission_control_widget.start_analysis_requested.connect(self._handle_mission_control_start)
        self.mission_control_widget.review_document_requested.connect(self._handle_mission_control_review)
        layout.addWidget(self.mission_control_widget)
        return tab

    def _create_log_stream_tab(self) -> QWidget:
        tab, layout = self._create_tab_base_layout()
        self.log_viewer = LogViewerWidget(tab)
        layout.addWidget(self.log_viewer)
        return tab

    def _create_admin_tab(self) -> QWidget:
        tab, layout = self._create_tab_base_layout()
        self.settings_editor = SettingsEditorWidget(tab)
        self.settings_editor.save_requested.connect(self.view_model.save_settings)
        layout.addWidget(self.settings_editor)
        return tab

    def _handle_mission_control_start(self) -> None:
        self.tab_widget.setCurrentWidget(self.analysis_summary_tab)
        self._prompt_for_document()

    def _handle_mission_control_review(self, doc_info: dict) -> None:
        doc_name = doc_info.get("title") or doc_info.get("name") or doc_info.get("document_name") or "Document"
        QMessageBox.information(self, "Review Document", f"Detailed replay for '{doc_name}' will be available in a future update.")

    def _create_analysis_summary_tab(self) -> QWidget:
        tab, layout = self._create_tab_base_layout(spacing=8)
        self.analysis_summary_browser = QTextBrowser(tab)
        self.analysis_summary_browser.setOpenExternalLinks(True)
        layout.addWidget(self.analysis_summary_browser, stretch=2)
        self.insights_browser = QTextBrowser(tab)
        self.insights_browser.setPlaceholderText("Insights and recommendations will appear here once the analysis completes.")
        layout.addWidget(self.insights_browser, stretch=1)
        return tab

    def _create_detailed_results_tab(self) -> QWidget:
        self.detailed_results_browser, tab = self._create_browser_tab()
        return tab

    def _create_dashboard_tab(self) -> QWidget:
        tab, layout = self._create_tab_base_layout()
        self.dashboard_widget = DashboardWidget() if DashboardWidget else QTextBrowser()
        if not DashboardWidget: self.dashboard_widget.setPlainText("Dashboard component unavailable.")
        layout.addWidget(self.dashboard_widget)
        return tab

    def _create_meta_tab(self) -> QWidget:
        tab, layout = self._create_tab_base_layout()
        self.meta_widget = MetaAnalyticsWidget() if MetaAnalyticsWidget else QTextBrowser()
        if not MetaAnalyticsWidget: self.meta_widget.setPlainText("Meta analytics component unavailable.")
        layout.addWidget(self.meta_widget)
        return tab

    def _create_report_tab(self) -> QWidget:
        self.report_preview_browser, tab = self._create_browser_tab()
        return tab

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
        status: QStatusBar = self.statusBar()
        status.showMessage("Ready")
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximumWidth(180)
        self.progress_bar.hide()
        status.addPermanentWidget(self.progress_bar)

    def _build_docks(self) -> None:
        self.document_preview_dock = QDockWidget("Document Preview", self)
        self.document_preview_dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.document_preview_browser = QTextBrowser(self.document_preview_dock)
        self.document_preview_dock.setWidget(self.document_preview_browser)
        self.addDockWidget(Qt.RightDockWidgetArea, self.document_preview_dock)

        if PerformanceStatusWidget:
            self.performance_dock = QDockWidget("Performance", self)
            self.performance_widget = PerformanceStatusWidget()
            self.performance_dock.setWidget(self.performance_widget)
            self.addDockWidget(Qt.RightDockWidgetArea, self.performance_dock)
        else:
            self.performance_dock = None

        self._build_auto_analysis_dock()

    def _build_auto_analysis_dock(self) -> None:
        self.auto_analysis_dock = QDockWidget("Auto-Analysis Queue", self)
        self.auto_analysis_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        self.auto_analysis_queue_list = QListWidget()
        layout.addWidget(self.auto_analysis_queue_list)
        
        process_button = QPushButton("Process Queue")
        process_button.clicked.connect(self._process_auto_analysis_queue)
        layout.addWidget(process_button)
        
        self.auto_analysis_dock.setWidget(container)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.auto_analysis_dock)
        self.auto_analysis_dock.setVisible(False) # Initially hidden

    def _build_floating_chat_button(self) -> None:
        self.chat_button = QPushButton("Ask AI Assistant", self)
        self.chat_button.setObjectName("floatingChatButton")
        self.chat_button.clicked.connect(self._open_chat_dialog)
        self.chat_button.setStyleSheet("""
            QPushButton#floatingChatButton {background-color: palette(highlight); color: palette(highlighted-text); border-radius: 22px; padding: 10px 20px; font-weight: bold;}
            QPushButton#floatingChatButton:hover {background-color: palette(light);}
        """)
        self.chat_button.resize(220, 44)
        self.chat_button.raise_()

    def _apply_theme(self, theme: str) -> None:
        QApplication.instance().setPalette(get_theme_palette(theme))
        for action in self.theme_action_group.actions():
            if action.text().lower() == theme: action.setChecked(True)

    def _save_gui_settings(self) -> None:
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("mainSplitter", self.main_splitter.saveState())
        if self.theme_action_group.checkedAction():
            self.settings.setValue("theme", self.theme_action_group.checkedAction().text().lower())
        self.settings.setValue("analysis/rubric", self.rubric_selector.currentData())
        if self._selected_file: self.settings.setValue("analysis/last_file", str(self._selected_file))

    def _load_gui_settings(self) -> None:
        if geometry := self.settings.value("geometry"): self.restoreGeometry(geometry)
        if window_state := self.settings.value("windowState"): self.restoreState(window_state)
        if splitter_state := self.settings.value("mainSplitter"): self.main_splitter.restoreState(splitter_state)
        saved_rubric = self.settings.value("analysis/rubric", type=str)
        if last_file := self.settings.value("analysis/last_file", type=str): self._set_selected_file(Path(last_file))

    def _prompt_for_document(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Select clinical document", str(Path.home()), "Documents (*.pdf *.docx *.txt *.md *.json)")
        if file_path: self._set_selected_file(Path(file_path))

    def _set_selected_file(self, file_path: Path) -> None:
        if not file_path.is_file():
            self.statusBar().showMessage(f"File not found: {file_path.name}", 5000)
            self._selected_file = None
            self.file_display.clear()
        else:
            self._selected_file = file_path
            self.file_display.setPlainText(self._selected_file.read_text(encoding='utf-8', errors='ignore')[:4000])
            self.statusBar().showMessage(f"Selected {self._selected_file.name}", 3000)
        self._update_document_preview()

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
        if not self._current_payload: QMessageBox.information(self, "No report", "Run an analysis before exporting a report."); return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save report", str(Path.home() / "compliance_report.html"), "HTML Files (*.html)")
        if not file_path: return
        Path(file_path).write_text(self.report_preview_browser.toHtml(), encoding='utf-8')
        self.statusBar().showMessage(f"Report exported to {file_path}", 5000)

    def _open_rubric_manager(self) -> None:
        dialog = RubricManagerDialog(self.auth_token, self)
        if dialog.exec(): self.view_model.load_rubrics()

    def _open_settings_dialog(self) -> None:
        dialog = SettingsDialog(self)
        dialog.exec()

    def _open_chat_dialog(self) -> None:
        initial_context = self.analysis_summary_browser.toPlainText() or "Provide a compliance summary."
        dialog = ChatDialog(initial_context, self.auth_token, self)
        dialog.exec()

    def _show_about_dialog(self) -> None:
        QMessageBox.information(self, "About", f"Therapy Compliance Analyzer\nWelcome, {self.current_user.username}!")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        margin = 24
        button_width = self.chat_button.width()
        button_height = self.chat_button.height()
        self.chat_button.move(self.width() - button_width - margin, self.height() - button_height - margin)

    def closeEvent(self, event) -> None:
        self._save_gui_settings()
        self.view_model.stop_all_workers()
        super().closeEvent(event)

__all__ = ["MainApplicationWindow"]
