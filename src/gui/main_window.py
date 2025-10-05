"""Primary GUI window for the Therapy Compliance Analyzer."""
from __future__ import annotations

import json
import os
import webbrowser
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
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
    QSlider,
    QSplitter,
    QSpinBox,
    QStatusBar,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.config import get_settings
from src.core.report_generator import ReportGenerator
from src.gui.dialogs.chat_dialog import ChatDialog
from src.gui.dialogs.rubric_manager_dialog import RubricManagerDialog
from src.gui.workers.analysis_starter_worker import AnalysisStarterWorker
from src.gui.workers.single_analysis_polling_worker import SingleAnalysisPollingWorker

try:  # Optional enhancements
    from src.gui.widgets.dashboard_widget import DashboardWidget
except Exception:  # pragma: no cover - optional dependency
    DashboardWidget = None  # type: ignore

try:
    from src.gui.widgets.meta_analytics_widget import MetaAnalyticsWidget
except Exception:  # pragma: no cover - optional dependency
    MetaAnalyticsWidget = None  # type: ignore

try:
    from src.gui.widgets.performance_status_widget import PerformanceStatusWidget
from src.gui.widgets.mission_control_widget import MissionControlWidget
except Exception:  # pragma: no cover - optional dependency
    PerformanceStatusWidget = None  # type: ignore


SETTINGS = get_settings()
API_URL = SETTINGS.paths.api_url


class MainApplicationWindow(QMainWindow):
    """Modernised main window that consolidates the disparate GUI variants."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Therapy Compliance Analyzer")
        self.resize(1440, 920)

        self.auth_token = os.environ.get("THERAPY_ANALYZER_TOKEN") or ""
        self._active_threads: list[QThread] = []
        self._poll_thread: Optional[QThread] = None
        self._poll_worker: Optional[SingleAnalysisPollingWorker] = None
        self._current_task_id: Optional[str] = None
        self._current_payload: Dict[str, Any] = {}
        self._selected_file: Optional[Path] = None

        self.report_generator = ReportGenerator()

        self._build_ui()
        self._load_initial_state()

    # ------------------------------------------------------------------
    # UI construction helpers
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self._build_menus()
        self._build_central_layout()
        self._build_status_bar()
        self._build_docks()
        self._build_floating_chat_button()
        self._apply_theme('light')

    def _build_menus(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        open_file_action = QAction("Open Document…", self)
        open_file_action.triggered.connect(self._prompt_for_document)
        file_menu.addAction(open_file_action)

        open_folder_action = QAction("Open Folder…", self)
        open_folder_action.triggered.connect(self._prompt_for_folder)
        file_menu.addAction(open_folder_action)

        export_action = QAction("Export Report…", self)
        export_action.triggered.connect(self._export_report)
        file_menu.addAction(export_action)
        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menu_bar.addMenu("&View")
        toggle_preview_action = QAction("Toggle Document Preview", self, checkable=True)
        toggle_preview_action.setChecked(True)
        toggle_preview_action.triggered.connect(self._toggle_document_preview)
        view_menu.addAction(toggle_preview_action)

        toggle_performance_action = QAction("Toggle Performance Panel", self, checkable=True)
        toggle_performance_action.setChecked(True)
        toggle_performance_action.triggered.connect(self._toggle_performance_panel)
        view_menu.addAction(toggle_performance_action)

        theme_menu = QMenu("Theme", self)
        for name in ("light", "dark"):
            action = QAction(name.capitalize(), self, checkable=True)
            action.triggered.connect(lambda checked, theme=name: self._apply_theme(theme))
            theme_menu.addAction(action)
        view_menu.addMenu(theme_menu)

        tools_menu = menu_bar.addMenu("&Tools")
        refresh_dashboards_action = QAction("Refresh Dashboards", self)
        refresh_dashboards_action.triggered.connect(self._refresh_dashboards)
        tools_menu.addAction(refresh_dashboards_action)

        refresh_meta_action = QAction("Refresh Meta Analytics", self)
        refresh_meta_action.triggered.connect(self._refresh_meta_analytics)
        tools_menu.addAction(refresh_meta_action)

        rubrics_action = QAction("Manage Rubrics…", self)
        rubrics_action.triggered.connect(self._open_rubric_manager)
        tools_menu.addAction(rubrics_action)

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

        self.file_display = QTextEdit(panel)
        self.file_display.setReadOnly(True)
        self.file_display.setMaximumHeight(80)
        self.file_display.setPlaceholderText("No document selected")
        layout.addWidget(self.file_display)

        controls_row = QHBoxLayout()
        self.open_file_button = QPushButton("Browse…", panel)
        self.open_file_button.clicked.connect(self._prompt_for_document)
        controls_row.addWidget(self.open_file_button)

        self.open_folder_button = QPushButton("Folder…", panel)
        self.open_folder_button.clicked.connect(self._prompt_for_folder)
        controls_row.addWidget(self.open_folder_button)
        layout.addLayout(controls_row)

        self.rubric_selector = QComboBox(panel)
        layout.addWidget(self.rubric_selector)

        settings_frame = QFrame(panel)
        settings_frame.setFrameShape(QFrame.StyledPanel)
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setSpacing(6)

        self.strict_mode_checkbox = QCheckBox("Enable strict compliance checks", settings_frame)
        settings_layout.addWidget(self.strict_mode_checkbox)
        self.generate_report_checkbox = QCheckBox("Generate printable report", settings_frame)
        self.generate_report_checkbox.setChecked(True)
        settings_layout.addWidget(self.generate_report_checkbox)

        slider_row = QHBoxLayout()
        slider_row.addWidget(QLabel("Sensitivity", settings_frame))
        self.sensitivity_slider = QSlider(Qt.Horizontal, settings_frame)
        self.sensitivity_slider.setRange(1, 10)
        self.sensitivity_slider.setValue(5)
        slider_row.addWidget(self.sensitivity_slider)
        settings_layout.addLayout(slider_row)

        layout.addWidget(settings_frame)

        self.quick_actions_list = QListWidget(panel)
        self.quick_actions_list.setMaximumHeight(140)
        for label in [
            "Pre-check medical necessity",
            "Verify plan of care",
            "Audit SOAP structure",
        ]:
            item = QListWidgetItem(label)
            item.setCheckState(Qt.Unchecked)
            self.quick_actions_list.addItem(item)
        layout.addWidget(self.quick_actions_list)

        self.analysis_button = QPushButton("Start Analysis", panel)
        self.analysis_button.setIcon(QIcon.fromTheme("media-playback-start"))
        self.analysis_button.clicked.connect(self._start_analysis)
        layout.addWidget(self.analysis_button)

        self.theme_combo = QComboBox(panel)
        self.theme_combo.addItems(["Light", "Dark"])
        self.theme_combo.currentTextChanged.connect(lambda name: self._apply_theme(name.lower()))
        layout.addWidget(self.theme_combo)

        layout.addStretch(1)
        return panel


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

    def _create_analysis_summary_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.analysis_summary_browser = QTextBrowser(tab)
        self.analysis_summary_browser.setOpenExternalLinks(True)
        layout.addWidget(self.analysis_summary_browser, stretch=2)

        self.insights_browser = QTextBrowser(tab)
        self.insights_browser.setPlaceholderText("Insights and recommendations will appear here once the analysis completes.")
        layout.addWidget(self.insights_browser, stretch=1)
        return tab

    def _create_detailed_results_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        self.detailed_results_browser = QTextBrowser(tab)
        layout.addWidget(self.detailed_results_browser)
        return tab

    def _create_dashboard_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        if DashboardWidget:
            self.dashboard_widget = DashboardWidget()
            layout.addWidget(self.dashboard_widget)
        else:
            placeholder = QTextBrowser(tab)
            placeholder.setPlainText("Dashboard component unavailable in this build.")
            layout.addWidget(placeholder)
            self.dashboard_widget = placeholder
        return tab

    def _create_meta_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        if MetaAnalyticsWidget:
            self.meta_widget = MetaAnalyticsWidget()
            layout.addWidget(self.meta_widget)
        else:
            placeholder = QTextBrowser(tab)
            placeholder.setPlainText("Meta analytics component unavailable in this build.")
            layout.addWidget(placeholder)
            self.meta_widget = placeholder
        return tab

    def _create_report_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        self.report_preview_browser = QTextBrowser(tab)
        layout.addWidget(self.report_preview_browser)
        return tab

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
            self.performance_widget = None

    def _build_floating_chat_button(self) -> None:
        self.chat_button = QPushButton("Ask AI Assistant", self)
        self.chat_button.setObjectName("floatingChatButton")
        self.chat_button.clicked.connect(self._open_chat_dialog)
        self.chat_button.setStyleSheet(
            """
            QPushButton#floatingChatButton {
                background-color: #0ea5e9;
                color: white;
                border-radius: 22px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton#floatingChatButton:hover {
                background-color: #0284c7;
            }
            """
        )
        self.chat_button.resize(220, 44)
        self.chat_button.raise_()

    # ------------------------------------------------------------------
    # Data loading & theme
    # ------------------------------------------------------------------
    def _load_initial_state(self) -> None:
        self._load_rubrics()
        QTimer.singleShot(250, self._refresh_dashboards)
        QTimer.singleShot(500, self._refresh_meta_analytics)

    def _apply_theme(self, theme: str) -> None:
        palette = QPalette()
        if theme == 'dark':
            palette.setColor(QPalette.Window, QColor(30, 34, 43))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(24, 26, 32))
            palette.setColor(QPalette.AlternateBase, QColor(30, 34, 43))
            palette.setColor(QPalette.ToolTipBase, Qt.white)
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(45, 49, 60))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.Highlight, QColor(14, 165, 233))
            palette.setColor(QPalette.HighlightedText, Qt.white)
        else:
            palette = QApplication.style().standardPalette()
        QApplication.instance().setPalette(palette)

    # ------------------------------------------------------------------
    # Control panel handlers
    # ------------------------------------------------------------------
    def _prompt_for_document(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select clinical document",
            str(Path.home()),
            "Documents (*.pdf *.docx *.txt *.md *.json)"
        )
        if not file_path:
            return
        self._selected_file = Path(file_path)
        self.file_display.setPlainText(self._selected_file.read_text(encoding='utf-8', errors='ignore')[:4000])
        self._update_document_preview()
        self.statusBar().showMessage(f"Selected {self._selected_file.name}", 3000)

    def _prompt_for_folder(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select folder containing documents",
            str(Path.home())
        )
        if folder_path:
            QMessageBox.information(
                self,
                "Folder selected",
                "Batch folder analysis will be supported in an upcoming revision."
            )

    def _start_analysis(self) -> None:
        if not self._selected_file:
            QMessageBox.warning(self, "No document", "Please select a document before starting the analysis.")
            return

        if not self.auth_token:
            QMessageBox.warning(
                self,
                "Authentication required",
                "Set the THERAPY_ANALYZER_TOKEN environment variable with a valid access token before running the analysis."
            )
            return

        payload = {
            "discipline": self.rubric_selector.currentData() or "",
            "analysis_mode": "rubric",
            "options": {
                "strict": self.strict_mode_checkbox.isChecked(),
                "sensitivity": self.sensitivity_slider.value(),
            },
        }

        worker = AnalysisStarterWorker(
            file_path=str(self._selected_file),
            data=payload,
            token=self.auth_token,
        )
        self.analysis_button.setEnabled(False)

        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.success.connect(self._handle_analysis_task_started)
        worker.error.connect(lambda message: self._handle_worker_error(message, thread))
        worker.success.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.finished.connect(lambda: self._active_threads.remove(thread))
        self._active_threads.append(thread)

        self.progress_bar.setRange(0, 0)
        self.progress_bar.show()
        self.statusBar().showMessage("Submitting document for analysis…")
        thread.start()

    def _handle_analysis_task_started(self, task_id: str) -> None:
        self._current_task_id = task_id
        self.statusBar().showMessage("Analysis running…")
        self._start_polling_worker(task_id)

    def _start_polling_worker(self, task_id: str) -> None:
        if self._poll_thread:
            self._stop_polling_worker()

        self._poll_worker = SingleAnalysisPollingWorker(task_id)
        self._poll_thread = QThread(self)
        self._poll_worker.moveToThread(self._poll_thread)
        self._poll_thread.started.connect(self._poll_worker.run)
        self._poll_worker.progress.connect(self._update_progress)
        self._poll_worker.success.connect(self._handle_analysis_success)
        self._poll_worker.error.connect(self._handle_analysis_error)
        self._poll_worker.finished.connect(self._handle_analysis_finished)
        self._poll_worker.finished.connect(self._poll_thread.quit)
        self._poll_thread.finished.connect(self._stop_polling_worker)
        self._poll_thread.start()

    def _stop_polling_worker(self) -> None:
        if self._poll_worker:
            self._poll_worker.stop()
        if self._poll_thread:
            self._poll_thread.deleteLater()
        self._poll_worker = None
        self._poll_thread = None

    def _handle_worker_error(self, message: str, thread: QThread) -> None:
        thread.deleteLater()
        QMessageBox.critical(self, "Analysis failed", message)
        self.analysis_button.setEnabled(True)
        self.progress_bar.hide()
        self.statusBar().showMessage("Analysis failed", 5000)

    def _update_progress(self, value: int) -> None:
        if self.progress_bar.maximum() == 0:
            self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(value)

    def _handle_analysis_success(self, payload: Dict[str, Any]) -> None:
        self.analysis_button.setEnabled(True)
        self._current_payload = payload
        report_html = payload.get("report_html")
        analysis = payload.get("analysis", {})

        if not report_html:
            report_html = self.report_generator.generate_html_report(
                analysis_result=analysis,
                doc_name=analysis.get("document_name", self._selected_file.name if self._selected_file else "Document"),
            )

        if report_html:
            self.analysis_summary_browser.setHtml(report_html)
            self.report_preview_browser.setHtml(report_html)
        else:
            self.analysis_summary_browser.setPlainText(json.dumps(payload, indent=2))

        self.insights_browser.setPlainText(
            json.dumps(analysis.get("insights", {}), indent=2) if analysis else "No insights generated."
        )
        self.detailed_results_browser.setPlainText(json.dumps(payload, indent=2))

        self.statusBar().showMessage("Analysis complete", 5000)
        self.progress_bar.hide()

    def _handle_analysis_error(self, message: str) -> None:
        QMessageBox.critical(self, "Analysis error", message)
        self.analysis_button.setEnabled(True)
        self.progress_bar.hide()
        self.statusBar().showMessage("Analysis error", 5000)

    def _handle_analysis_finished(self) -> None:
        self._stop_polling_worker()
        self.progress_bar.hide()
        self.analysis_button.setEnabled(True)

    # ------------------------------------------------------------------
def _handle_mission_control_start(self) -> None:
    self.tab_widget.setCurrentWidget(self.analysis_summary_tab)
    self._prompt_for_document()

def _handle_mission_control_review(self, doc_info: dict) -> None:
    doc_name = doc_info.get("title") or doc_info.get("name") or doc_info.get("document_name") or "Document"
    QMessageBox.information(
        self,
        "Review Document",
        f"Detailed replay for '{doc_name}' will be available in a future update."
    )

# ------------------------------------------------------------------
    # Auxiliary actions
    # ------------------------------------------------------------------
    def _update_document_preview(self) -> None:
        if not self._selected_file:
            self.document_preview_browser.clear()
            return
        suffix = self._selected_file.suffix.lower()
        if suffix in {'.txt', '.md', '.json', '.yaml', '.csv'}:
            content = self._selected_file.read_text(encoding='utf-8', errors='ignore')
            self.document_preview_browser.setPlainText(content[:10000])
        else:
            self.document_preview_browser.setHtml(
                f"<h3>Preview unavailable</h3><p>{self._selected_file.name} cannot be previewed in-app.</p>"
            )

    def _load_rubrics(self) -> None:
        self.rubric_selector.clear()
        try:
            response = requests.get(f"{API_URL}/rubrics", timeout=4)
            response.raise_for_status()
            rubrics = response.json()
        except requests.RequestException:
            rubrics = [
                {"name": "Physical Therapy", "value": "pt"},
                {"name": "Occupational Therapy", "value": "ot"},
                {"name": "Speech Therapy", "value": "st"},
            ]
        for rubric in rubrics:
            self.rubric_selector.addItem(rubric.get("name", "Unnamed rubric"), rubric.get("value"))

    def _refresh_dashboards(self) -> None:
        if not self.dashboard_widget:
            return
        try:
            response = requests.get(f"{API_URL}/dashboard/overview", timeout=4)
            response.raise_for_status()
            data = response.json()
            if hasattr(self.dashboard_widget, "load_data"):
                self.dashboard_widget.load_data(data)  # type: ignore[func-attr]
            elif isinstance(self.dashboard_widget, QTextBrowser):
                self.dashboard_widget.setPlainText(json.dumps(data, indent=2))
        except requests.RequestException:
            if isinstance(self.dashboard_widget, QTextBrowser):
                self.dashboard_widget.setPlainText("Dashboard data unavailable.")

    def _refresh_meta_analytics(self) -> None:
        if not self.meta_widget:
            return
        try:
            response = requests.get(f"{API_URL}/dashboard/meta", timeout=4)
            response.raise_for_status()
            data = response.json()
            if hasattr(self.meta_widget, "load_data"):
                self.meta_widget.load_data(data)  # type: ignore[func-attr]
            elif isinstance(self.meta_widget, QTextBrowser):
                self.meta_widget.setPlainText(json.dumps(data, indent=2))
        except requests.RequestException:
            if isinstance(self.meta_widget, QTextBrowser):
                self.meta_widget.setPlainText("Meta analytics unavailable.")

    def _export_report(self) -> None:
        if not self._current_payload:
            QMessageBox.information(self, "No report", "Run an analysis before exporting a report.")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save report",
            str(Path.home() / "compliance_report.html"),
            "HTML Files (*.html)"
        )
        if not file_path:
            return
        html = self.report_preview_browser.toHtml()
        Path(file_path).write_text(html, encoding='utf-8')
        self.statusBar().showMessage(f"Report exported to {file_path}", 5000)

    def _toggle_document_preview(self, checked: bool) -> None:
        self.document_preview_dock.setVisible(checked)

    def _toggle_performance_panel(self, checked: bool) -> None:
        if self.performance_dock:
            self.performance_dock.setVisible(checked)

    def _open_rubric_manager(self) -> None:
        dialog = RubricManagerDialog(self)
        dialog.exec()
        self._load_rubrics()

    def _open_chat_dialog(self) -> None:
        dialog = ChatDialog("Provide a compliance summary", "", self)
        dialog.exec()

    def _show_about_dialog(self) -> None:
        QMessageBox.information(
            self,
            "About",
            "Therapy Compliance Analyzer\n"
            "Advanced GUI consolidating legacy windows into a single experience."
        )

    # ------------------------------------------------------------------
    # Qt overrides
    # ------------------------------------------------------------------
    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        margin = 24
        button_width = self.chat_button.width()
        button_height = self.chat_button.height()
        self.chat_button.move(
            self.width() - button_width - margin,
            self.height() - button_height - margin,
        )

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._stop_polling_worker()
        for thread in list(self._active_threads):
            thread.quit()
            thread.wait(150)
        super().closeEvent(event)


__all__ = ["MainApplicationWindow"]
