
"""Primary GUI window for the Therapy Compliance Analyzer."""
from __future__ import annotations

import functools
import json
import logging
import webbrowser
import requests
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type, Protocol
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

from PySide6.QtCore import Qt, QThread, QSettings, QObject, Signal, QUrl
from PySide6.QtGui import QAction, QFont, QActionGroup
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
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

# Import minimal micro-interactions (subtle animations only)
from src.gui.widgets.micro_interactions import AnimatedButton, LoadingSpinner

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
        """Stop all worker threads quickly - don't wait too long."""
        for thread in list(self._active_threads):
            try:
                if thread.isRunning():
                    thread.quit()
                    thread.wait(100)  # Wait max 100ms per thread
                    if thread.isRunning():
                        thread.terminate()  # Force terminate if still running
            except Exception:
                pass
        self._active_threads.clear()


class MainApplicationWindow(QMainWindow):
    """The main application window (View)."""

    def __init__(self, user: models.User, token: str) -> None:
        super().__init__()
        self.setWindowTitle("THERAPY DOCUMENTATION COMPLIANCE ANALYSIS")
        self.resize(1440, 920)
        self.setMinimumSize(900, 600)  # Allow smaller scaling

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
        """Apply the comprehensive medical theme styling with better contrast."""
        # Apply main window stylesheet with softer background
        main_style = """
            QMainWindow {
                background-color: #f1f5f9;
            }
            QWidget {
                font-family: "Segoe UI", Arial, sans-serif;
            }
        """
        self.setStyleSheet(main_style)
        
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
        
        # Simulate AI model loading (set all to loading state initially)
        self.status_component.set_all_loading()
        
        # After a short delay, set all models as ready (in production, this would be based on actual model loading)
        # For now, we'll set them as ready after 2 seconds
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, self._on_ai_models_ready)

    def _on_ai_models_ready(self) -> None:
        """Called when AI models are loaded and ready."""
        self.status_component.set_all_ready()
        status_text = self.status_component.get_status_text()
        self.statusBar().showMessage(f"✅ {status_text}", 5000)

    def _start_analysis(self) -> None:
        if not self._selected_file:
            QMessageBox.warning(self, "No Document", "Please select a document before starting the analysis.")
            return
        
        # Check if rubric is selected
        if not self.rubric_selector.currentData():
            QMessageBox.warning(self, "No Rubric", "Please select a compliance guideline before analysis.")
            return
        
        options = {
            "discipline": self.rubric_selector.currentData() or "",
            "analysis_mode": "rubric",
        }
        self.run_analysis_button.setEnabled(False)
        self.repeat_analysis_button.setEnabled(False)
        
        # Show subtle loading spinner
        self.loading_spinner.start_spinning()
        self.statusBar().showMessage("⏳ Starting analysis... This may take a moment.", 0)
        
        try:
            self.view_model.start_analysis(str(self._selected_file), options)
        except Exception as e:
            self.loading_spinner.stop_spinning()
            self.run_analysis_button.setEnabled(True)
            self.repeat_analysis_button.setEnabled(True)
            QMessageBox.critical(self, "Analysis Error", f"Failed to start analysis:\n{str(e)}\n\nMake sure the API server is running.")
            self.statusBar().showMessage("❌ Analysis failed to start", 5000)

    def _repeat_analysis(self) -> None:
        """Repeat analysis on the same document with current settings."""
        if not self._selected_file:
            QMessageBox.warning(self, "No document", "No document selected to repeat analysis.")
            return
        
        self.statusBar().showMessage("Repeating analysis...", 2000)
        self._start_analysis()

    def _on_strictness_selected(self, selected_button: AnimatedButton) -> None:
        """Handle strictness level selection (only one can be selected at a time)."""
        for btn in self.strictness_buttons:
            if btn != selected_button:
                btn.setChecked(False)
        selected_button.setChecked(True)
        
        # Get selected level
        level = selected_button.text().split()[-1]  # Extract level name
        self.statusBar().showMessage(f"Review strictness set to: {level}", 3000)

    def _open_report_popup(self) -> None:
        """Open the full report in a popup window."""
        if not self._current_payload:
            QMessageBox.information(self, "No Report", "No analysis report available yet. Please run an analysis first.")
            return
        
        # Create popup dialog
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("📊 Compliance Analysis Report")
        dialog.resize(1000, 700)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Report browser
        report_browser = QTextBrowser(dialog)
        report_browser.setOpenExternalLinks(False)
        report_browser.anchorClicked.connect(self._handle_link_clicked)
        
        # Load report
        analysis = self._current_payload.get("analysis", {})
        doc_name = self._selected_file.name if self._selected_file else "Document"
        report_html = self._current_payload.get("report_html") or self.report_generator.generate_html_report(
            analysis_result=analysis, doc_name=doc_name
        )
        report_browser.setHtml(report_html)
        
        layout.addWidget(report_browser)
        
        # Close button
        close_btn = AnimatedButton("✖️ Close", dialog)
        close_btn.clicked.connect(dialog.close)
        close_btn.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        layout.addWidget(close_btn)
        
        dialog.exec()

    def _toggle_all_sections(self, checked: bool) -> None:
        """Toggle all report section checkboxes."""
        for checkbox in self.section_checkboxes.values():
            checkbox.setChecked(checked)
        
        status = "selected" if checked else "deselected"
        self.statusBar().showMessage(f"All sections {status}", 2000)

    def _open_document_preview(self) -> None:
        """Open document preview in a popup window."""
        if not self._selected_file:
            QMessageBox.information(self, "No Document", "No document selected to preview.")
            return
        
        # Create popup dialog
        from PySide6.QtWidgets import QDialog
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"📄 Document Preview - {self._selected_file.name}")
        dialog.resize(900, 700)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Document browser
        doc_browser = QTextBrowser(dialog)
        doc_browser.setPlainText(self._cached_preview_content or "Loading document...")
        layout.addWidget(doc_browser)
        
        # Close button
        close_btn = AnimatedButton("✖️ Close", dialog)
        close_btn.clicked.connect(dialog.close)
        close_btn.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        layout.addWidget(close_btn)
        
        dialog.exec()

    def _export_report_pdf(self) -> None:
        """Export the current report as PDF."""
        if not self._current_payload:
            QMessageBox.information(self, "No Report", "No analysis report available to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Report as PDF", "", "PDF Files (*.pdf)"
        )
        
        if file_path:
            try:
                from src.core.pdf_export_service import PDFExportService
                from pathlib import Path
                import shutil
                
                # Get HTML content from current payload
                html_content = self._current_payload.get("report_html", "")
                if not html_content:
                    QMessageBox.warning(self, "No Content", "Report HTML content not available.")
                    return
                
                # Initialize PDF export service
                pdf_service = PDFExportService(output_dir="temp/reports")
                
                # Get document name for metadata
                doc_name = self._current_payload.get("document_name", "Compliance Report")
                
                # Export to PDF
                result = pdf_service.export_to_pdf(
                    html_content=html_content,
                    document_name=doc_name,
                    filename=Path(file_path).stem,
                    metadata={
                        "title": f"Compliance Analysis - {doc_name}",
                        "author": "Therapy Compliance Analyzer",
                        "subject": "Clinical Documentation Compliance Report"
                    }
                )
                
                if result["success"]:
                    # Copy the generated PDF to the user's chosen location
                    shutil.copy2(result["pdf_path"], file_path)
                    
                    self.statusBar().showMessage(f"✅ Report exported to: {file_path}", 5000)
                    QMessageBox.information(self, "Export Successful", f"Report exported successfully to:\n{file_path}")
                else:
                    error_msg = result.get("error", "Unknown error occurred")
                    QMessageBox.warning(self, "Export Failed", f"PDF export failed:\n{error_msg}\n\nTip: Install weasyprint for better PDF support:\npip install weasyprint")
                    
            except Exception as e:
                logger.error(f"PDF export failed: {e}")
                QMessageBox.warning(self, "Export Failed", f"Failed to export report: {str(e)}\n\nTip: Install weasyprint:\npip install weasyprint")

    def _export_report_html(self) -> None:
        """Export the current report as HTML."""
        if not self._current_payload:
            QMessageBox.information(self, "No Report", "No analysis report available to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Report as HTML", "", "HTML Files (*.html)"
        )
        
        if file_path:
            try:
                analysis = self._current_payload.get("analysis", {})
                doc_name = self._selected_file.name if self._selected_file else "Document"
                report_html = self._current_payload.get("report_html") or self.report_generator.generate_html_report(
                    analysis_result=analysis, doc_name=doc_name
                )
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_html)
                
                self.statusBar().showMessage(f"✅ Report exported to: {file_path}", 5000)
                QMessageBox.information(self, "Export Successful", f"Report exported successfully to:\n{file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Export Failed", f"Failed to export report: {str(e)}")

    def _handle_analysis_success(self, payload: Dict[str, Any]) -> None:
        # Hide loading spinner
        self.loading_spinner.stop_spinning()
        
        self.statusBar().showMessage("✅ Analysis Complete - Click 'View Report' to see results", 5000)
        self.run_analysis_button.setEnabled(True)
        self.repeat_analysis_button.setEnabled(True)
        self.view_report_button.setEnabled(True)
        self._current_payload = payload
        
        # Display human-readable summary in results tab
        analysis = payload.get("analysis", {})
        doc_name = self._selected_file.name if self._selected_file else "Document"
        
        # Create human-readable summary
        summary_text = f"""
ANALYSIS COMPLETE
================

Document: {doc_name}
Status: ✅ Analysis Successful
Timestamp: {payload.get('timestamp', 'N/A')}

SUMMARY:
--------
Total Findings: {len(analysis.get('findings', []))}
Compliance Score: {analysis.get('compliance_score', 'N/A')}%
Risk Level: {analysis.get('risk_level', 'N/A')}

Click the "📊 View Report" button to see the full detailed report.

You can also:
- Click "🔄 Repeat" to run analysis again
- Click "📄 Export PDF" or "🌐 Export HTML" to save the report
        """
        
        self.analysis_summary_browser.setPlainText(summary_text)
        self.detailed_results_browser.setPlainText(json.dumps(payload, indent=2))
        
        self.view_model.load_dashboard_data() # Refresh dashboard after analysis

    def on_analysis_error(self, message: str) -> None:
        """Handles analysis errors by re-enabling controls and surfacing the status."""
        # Hide loading spinner
        self.loading_spinner.stop_spinning()
        
        self.statusBar().showMessage(f"Analysis failed: {message}", 5000)
        self.run_analysis_button.setEnabled(True)
        self.repeat_analysis_button.setEnabled(True)

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


    def _handle_report_link(self, url: QUrl) -> None:
        """Route analysis browser anchor clicks through the shared handler."""
        self._handle_link_clicked(url)

    def closeEvent(self, event) -> None:
        """Handle application close - exit quickly."""
        try:
            self._save_gui_settings()
        except Exception:
            pass  # Don't block exit on save errors
        
        # Force quit workers quickly
        try:
            self.view_model.stop_all_workers()
        except Exception:
            pass
        
        # Force terminate any remaining threads
        QApplication.quit()
        event.accept()

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
        
        # Optional docks (hidden by default)
        if self.performance_dock:
            view_menu.addAction(self.performance_dock.toggleViewAction())
        
        view_menu.addSeparator()
        
        # Theme submenu
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
        
        # Add beautiful medical-themed header at the top
        root_layout.addWidget(self.header)
        
        # Create main tab widget with modern styling (no chat tab - integrated into analysis)
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setDocumentMode(False)
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                background: {medical_theme.get_color('bg_primary')};
                top: -2px;
            }}
            QTabBar::tab {{
                background: {medical_theme.get_color('bg_secondary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-bottom: none;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                padding: 12px 24px;
                margin-right: 6px;
                color: {medical_theme.get_color('text_secondary')};
                font-weight: 700;
                font-size: 12px;
                min-width: 120px;
            }}
            QTabBar::tab:selected {{
                background: white;
                color: {medical_theme.get_color('primary_blue')};
                border-bottom: 2px solid white;
                margin-bottom: -2px;
            }}
            QTabBar::tab:hover:!selected {{
                background: {medical_theme.get_color('hover_bg')};
                color: {medical_theme.get_color('primary_blue')};
            }}
        """)
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
        """Create the Analysis tab with improved layout and scaling."""
        tab = QWidget(self)
        main_layout = QHBoxLayout(tab)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Left column: Rubric Selection (25%)
        left_column = self._create_rubric_selection_panel()
        main_layout.addWidget(left_column, stretch=25)
        
        # Middle column: Compliance Guidelines & Report Sections (30%)
        middle_column = self._create_middle_column_panel()
        main_layout.addWidget(middle_column, stretch=30)
        
        # Right column: Analysis Results with Chat (45%)
        right_column = self._create_analysis_results_with_chat()
        main_layout.addWidget(right_column, stretch=45)
        
        return tab
    
    def _create_rubric_selection_panel(self) -> QWidget:
        """Create left panel with rubric selection and document upload."""
        from PySide6.QtWidgets import QSizePolicy
        
        panel = QWidget(self)
        panel.setMinimumWidth(280)
        panel.setMaximumWidth(400)
        panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Document Upload Section
        upload_section = self._create_document_upload_section()
        layout.addWidget(upload_section)
        
        # Rubric Selection Section (moved here from middle)
        rubric_section = self._create_rubric_selector_section()
        layout.addWidget(rubric_section)
        
        # Action Buttons
        actions_section = self._create_action_buttons_section()
        layout.addWidget(actions_section)
        
        layout.addStretch(1)
        return panel
    
    def _create_rubric_selector_section(self) -> QWidget:
        """Create rubric selector section."""
        section = QWidget(self)
        section.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("📚 Select Rubric", section)
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')}; background: transparent; border: none;")
        layout.addWidget(title)
        
        # Rubric selector
        self.rubric_selector = QComboBox(section)
        self.rubric_selector.setMinimumHeight(40)
        self.rubric_selector.setStyleSheet(f"""
            QComboBox {{
                padding: 10px 12px;
                border: 2px solid {medical_theme.get_color('border_medium')};
                border-radius: 8px;
                background: white;
                font-size: 11px;
                font-weight: 500;
                color: {medical_theme.get_color('text_primary')};
            }}
            QComboBox:hover {{
                border-color: {medical_theme.get_color('primary_blue')};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 35px;
            }}
        """)
        layout.addWidget(self.rubric_selector)
        
        return section
    
    def _create_middle_column_panel(self) -> QWidget:
        """Create middle panel with compliance guidelines and report sections."""
        from PySide6.QtWidgets import QSizePolicy
        
        panel = QWidget(self)
        panel.setMinimumWidth(300)
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Compliance Guidelines Section (moved from left, above report sections)
        guidelines_section = self._create_compliance_guidelines_section()
        layout.addWidget(guidelines_section, stretch=1)
        
        # Report Sections (moved from middle)
        report_section = self._create_report_sections_panel()
        layout.addWidget(report_section, stretch=1)
        
        return panel
    
    def _create_compliance_guidelines_section(self) -> QWidget:
        """Create compliance guidelines section with smaller buttons."""
        
        section = QWidget(self)
        section.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("⚙️ Review Strictness", section)
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')}; background: transparent; border: none;")
        layout.addWidget(title)
        
        # Strictness buttons (smaller)
        strictness_layout = QHBoxLayout()
        strictness_layout.setSpacing(8)
        self.strictness_buttons = []
        
        for level, emoji in [("Lenient", "😊"), ("Standard", "📋"), ("Strict", "🔍")]:
            btn = AnimatedButton(f"{emoji}\n{level}", section)
            btn.setCheckable(True)
            btn.setMinimumHeight(45)  # Smaller than before (was 55)
            btn.setMaximumHeight(50)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: white;
                    border: 2px solid {medical_theme.get_color('border_medium')};
                    border-radius: 8px;
                    color: {medical_theme.get_color('text_primary')};
                    font-size: 10px;
                    font-weight: 600;
                    padding: 4px;
                }}
                QPushButton:hover {{
                    background-color: {medical_theme.get_color('hover_bg')};
                    border-color: {medical_theme.get_color('primary_blue')};
                }}
                QPushButton:checked {{
                    background-color: {medical_theme.get_color('primary_blue')};
                    color: white;
                    border-color: {medical_theme.get_color('primary_blue')};
                }}
            """)
            btn.clicked.connect(lambda checked, b=btn: self._on_strictness_selected(b))
            self.strictness_buttons.append(btn)
            strictness_layout.addWidget(btn)
        
        layout.addLayout(strictness_layout)
        
        # Set default to Standard
        if len(self.strictness_buttons) >= 2:
            self.strictness_buttons[1].setChecked(True)
        
        return section
    
    def _create_report_sections_panel(self) -> QWidget:
        """Create report sections panel."""
        from PySide6.QtWidgets import QCheckBox, QGridLayout
        
        section = QWidget(self)
        section.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("📋 Report Sections", section)
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')}; background: transparent; border: none;")
        layout.addWidget(title)
        
        # Checkboxes in grid
        grid = QGridLayout()
        grid.setSpacing(8)
        
        sections = [
            "Executive Summary", "Detailed Findings",
            "Risk Assessment", "Recommendations",
            "Regulatory Citations", "Action Plan",
            "AI Transparency", "Improvement Strategies"
        ]
        
        self.section_checkboxes = {}
        for i, section_name in enumerate(sections):
            checkbox = QCheckBox(section_name)
            checkbox.setChecked(True)
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    color: {medical_theme.get_color('text_primary')};
                    font-size: 10px;
                    spacing: 6px;
                    background: transparent;
                    border: none;
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                    border: 2px solid {medical_theme.get_color('border_medium')};
                    border-radius: 4px;
                    background: white;
                }}
                QCheckBox::indicator:checked {{
                    background: {medical_theme.get_color('primary_blue')};
                    border-color: {medical_theme.get_color('primary_blue')};
                }}
            """)
            self.section_checkboxes[section_name] = checkbox
            grid.addWidget(checkbox, i // 2, i % 2)
        
        layout.addLayout(grid)
        
        # Export buttons
        export_layout = QHBoxLayout()
        export_layout.setSpacing(8)
        
        pdf_btn = AnimatedButton("📄 PDF", section)
        pdf_btn.clicked.connect(self._export_report_pdf)
        pdf_btn.setMinimumHeight(35)
        pdf_btn.setStyleSheet(medical_theme.get_button_stylesheet("primary"))
        export_layout.addWidget(pdf_btn)
        
        html_btn = AnimatedButton("🌐 HTML", section)
        html_btn.clicked.connect(self._export_report_html)
        html_btn.setMinimumHeight(35)
        html_btn.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        export_layout.addWidget(html_btn)
        
        layout.addLayout(export_layout)
        
        return section
    
    def _create_analysis_results_with_chat(self) -> QWidget:
        """Create right panel with analysis results and integrated chat bar."""
        panel = QWidget(self)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Analysis results (existing)
        results_panel = self._create_analysis_right_panel_content()
        layout.addWidget(results_panel, stretch=1)
        
        # Chat input bar at bottom
        chat_bar = self._create_chat_input_bar()
        layout.addWidget(chat_bar, stretch=0)
        
        return panel
    
    def _create_analysis_right_panel_content(self) -> QWidget:
        """Create the analysis results content."""
        from PySide6.QtWidgets import QTabWidget
        
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Modern styled tabs
        results_tabs = QTabWidget(panel)
        results_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 8px;
                background: white;
                top: -1px;
            }}
            QTabBar::tab {{
                background: {medical_theme.get_color('bg_secondary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 10px 20px;
                margin-right: 4px;
                color: {medical_theme.get_color('text_secondary')};
                font-weight: 600;
                font-size: 11px;
            }}
            QTabBar::tab:selected {{
                background: white;
                color: {medical_theme.get_color('primary_blue')};
                border-bottom: 2px solid white;
            }}
            QTabBar::tab:hover {{
                background: {medical_theme.get_color('hover_bg')};
            }}
        """)
        
        # Summary tab
        self.analysis_summary_browser = QTextBrowser(panel)
        self.analysis_summary_browser.setOpenExternalLinks(False)
        self.analysis_summary_browser.anchorClicked.connect(self._handle_report_link)
        self.analysis_summary_browser.setStyleSheet("""
            QTextBrowser {
                border: none;
                background: white;
                padding: 15px;
                font-size: 12px;
                line-height: 1.6;
            }
        """)
        results_tabs.addTab(self.analysis_summary_browser, "📊 Summary")
        
        # Detailed results tab
        self.detailed_results_browser = QTextBrowser(panel)
        self.detailed_results_browser.setOpenExternalLinks(False)
        self.detailed_results_browser.anchorClicked.connect(self._handle_report_link)
        self.detailed_results_browser.setStyleSheet("""
            QTextBrowser {
                border: none;
                background: white;
                padding: 15px;
                font-size: 12px;
            }
        """)
        results_tabs.addTab(self.detailed_results_browser, "📋 Details")
        
        layout.addWidget(results_tabs)
        return panel
    
    def _create_chat_input_bar(self) -> QWidget:
        """Create chat input bar below analysis results."""
        bar = QWidget(self)
        bar.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color('bg_secondary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        bar.setMaximumHeight(60)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Chat input field
        self.chat_input = QTextEdit(bar)
        self.chat_input.setPlaceholderText("💬 Ask AI about the analysis results...")
        self.chat_input.setMaximumHeight(40)
        self.chat_input.setStyleSheet(f"""
            QTextEdit {{
                border: 2px solid {medical_theme.get_color('border_medium')};
                border-radius: 6px;
                padding: 8px;
                background: white;
                font-size: 11px;
                color: {medical_theme.get_color('text_primary')};
            }}
            QTextEdit:focus {{
                border-color: {medical_theme.get_color('primary_blue')};
            }}
        """)
        layout.addWidget(self.chat_input, stretch=1)
        
        # Send button
        send_btn = AnimatedButton("Send", bar)
        send_btn.setMinimumWidth(80)
        send_btn.setMaximumHeight(40)
        send_btn.clicked.connect(self._send_chat_message)
        send_btn.setStyleSheet(medical_theme.get_button_stylesheet("primary"))
        layout.addWidget(send_btn)
        
        return bar
    
    def _send_chat_message(self):
        """Handle sending chat message."""
        message = self.chat_input.toPlainText().strip()
        if not message:
            return
        
        # Clear input
        self.chat_input.clear()
        
        # Open chat dialog with the message
        self._open_chat_dialog(initial_message=message)
    
    def _create_analysis_left_column(self) -> QWidget:
        """Create the left column with document upload and settings."""
        from PySide6.QtWidgets import QSizePolicy
        
        column = QWidget(self)
        column.setMinimumWidth(350)
        column.setMaximumWidth(450)
        column.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Document Upload Section
        upload_section = self._create_document_upload_section()
        layout.addWidget(upload_section, stretch=0)
        
        # Analysis Settings Section
        settings_section = self._create_analysis_settings_section()
        layout.addWidget(settings_section, stretch=0)
        
        # Action Buttons Section
        actions_section = self._create_action_buttons_section()
        layout.addWidget(actions_section, stretch=0)
        
        layout.addStretch(1)
        return column
    
    def _create_document_upload_section(self) -> QWidget:
        """Create the document upload section."""
        section = QWidget(self)
        section.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📁 Upload Document", section)
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')}; background: transparent; border: none;")
        layout.addWidget(title)
        
        # File display
        self.file_display = QTextEdit(section)
        self.file_display.setReadOnly(True)
        self.file_display.setMinimumHeight(90)
        self.file_display.setMaximumHeight(110)
        self.file_display.setPlaceholderText("No document selected\n\nClick 'Upload Document' below")
        self.file_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: {medical_theme.get_color("bg_primary")};
                border: 2px dashed {medical_theme.get_color("border_medium")};
                border-radius: 8px;
                padding: 12px;
                font-size: 11px;
                color: {medical_theme.get_color("text_secondary")};
            }}
        """)
        layout.addWidget(self.file_display)
        
        # Upload buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.open_file_button = AnimatedButton("📄 Upload Document", section)
        self.open_file_button.clicked.connect(self._prompt_for_document)
        self.open_file_button.setStyleSheet(medical_theme.get_button_stylesheet("primary"))
        self.open_file_button.setMinimumHeight(42)
        buttons_layout.addWidget(self.open_file_button)
        
        self.open_folder_button = AnimatedButton("📂 Batch", section)
        self.open_folder_button.clicked.connect(self._prompt_for_folder)
        self.open_folder_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        self.open_folder_button.setMinimumHeight(42)
        self.open_folder_button.setMaximumWidth(100)
        buttons_layout.addWidget(self.open_folder_button)
        
        layout.addLayout(buttons_layout)
        return section

    def _create_analysis_settings_section(self) -> QWidget:
        """Create the analysis settings section with rubric and strictness."""
        section = QWidget(self)
        section.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)
        
        # Title
        title = QLabel("📋 Compliance Guidelines", section)
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')}; background: transparent; border: none;")
        layout.addWidget(title)
        
        # Rubric selector with better styling
        rubric_label = QLabel("Select Guidelines:", section)
        rubric_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        rubric_label.setStyleSheet("background: transparent; border: none; color: #475569;")
        layout.addWidget(rubric_label)
        
        self.rubric_selector = QComboBox(section)
        self.rubric_selector.setMinimumHeight(45)
        self.rubric_selector.setStyleSheet(f"""
            QComboBox {{
                padding: 12px 14px;
                border: 2px solid {medical_theme.get_color('border_medium')};
                border-radius: 8px;
                background: {medical_theme.get_color('bg_primary')};
                font-size: 12px;
                font-weight: 500;
                color: {medical_theme.get_color('text_primary')};
            }}
            QComboBox:hover {{
                border-color: {medical_theme.get_color('primary_blue')};
                background: white;
            }}
            QComboBox:focus {{
                border-color: {medical_theme.get_color('primary_blue')};
                border-width: 2px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 40px;
            }}
            QComboBox::down-arrow {{
                width: 14px;
                height: 14px;
            }}
        """)
        layout.addWidget(self.rubric_selector)
        
        # Separator
        separator = QWidget(section)
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {medical_theme.get_color('border_light')}; border: none; margin: 8px 0px;")
        layout.addWidget(separator)
        
        # Strictness selector
        strictness_label = QLabel("Review Strictness:", section)
        strictness_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        strictness_label.setStyleSheet("background: transparent; border: none; color: #475569;")
        layout.addWidget(strictness_label)
        
        strictness_layout = QHBoxLayout()
        strictness_layout.setSpacing(10)
        self.strictness_buttons = []
        
        for level, emoji in [("Moderate", "😊"), ("Standard", "📋"), ("Strict", "🔍")]:
            btn = AnimatedButton(f"{emoji}\n{level}", section)
            btn.setCheckable(True)
            btn.setMinimumHeight(55)
            btn.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
            btn.clicked.connect(lambda checked, b=btn: self._on_strictness_selected(b))
            strictness_layout.addWidget(btn)
            self.strictness_buttons.append(btn)
        
        self.strictness_buttons[1].setChecked(True)
        layout.addLayout(strictness_layout)
        
        return section

    def _create_action_buttons_section(self) -> QWidget:
        """Create the action buttons section."""
        section = QWidget(self)
        section.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Run Analysis button (big and prominent)
        self.run_analysis_button = AnimatedButton("▶️  Run Compliance Analysis", section)
        self.run_analysis_button.clicked.connect(self._start_analysis)
        self.run_analysis_button.setEnabled(False)
        self.run_analysis_button.setStyleSheet(medical_theme.get_button_stylesheet("success"))
        self.run_analysis_button.setMinimumHeight(55)
        self.run_analysis_button.setFont(QFont("Segoe UI", 13, QFont.Bold))
        layout.addWidget(self.run_analysis_button)
        
        # Secondary actions
        secondary_layout = QHBoxLayout()
        secondary_layout.setSpacing(10)
        
        self.repeat_analysis_button = AnimatedButton("🔄 Repeat", section)
        self.repeat_analysis_button.clicked.connect(self._repeat_analysis)
        self.repeat_analysis_button.setEnabled(False)
        self.repeat_analysis_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        self.repeat_analysis_button.setMinimumHeight(42)
        secondary_layout.addWidget(self.repeat_analysis_button)
        
        self.view_report_button = AnimatedButton("📊 View Report", section)
        self.view_report_button.clicked.connect(self._open_report_popup)
        self.view_report_button.setEnabled(False)
        self.view_report_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        self.view_report_button.setMinimumHeight(42)
        secondary_layout.addWidget(self.view_report_button)
        
        layout.addLayout(secondary_layout)
        return section


    def _create_report_outputs_panel(self) -> QWidget:
        """Create the Report Sections panel with grid of checkboxes."""
        panel = QWidget(self)
        panel.setStyleSheet(f"""
            QWidget {{
                background-color: {medical_theme.get_color("bg_secondary")};
                border: 2px solid {medical_theme.get_color("border_light")};
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("📋 Report Sections", panel)
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')}; background: transparent; border: none;")
        layout.addWidget(title)
        
        # Grid of checkboxes (2 columns)
        from PySide6.QtWidgets import QCheckBox, QGridLayout
        
        grid_widget = QWidget(panel)
        grid_widget.setStyleSheet("background: transparent; border: none;")
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(10)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Report sections
        sections = [
            ("✅ Medicare Guidelines", "medicare"),
            ("💪 Strengths", "strengths"),
            ("⚠️ Weaknesses", "weaknesses"),
            ("💡 Suggestions", "suggestions"),
            ("📚 Education", "education"),
            ("🎯 7 Habits", "habits"),
            ("📊 Compliance Score", "score"),
            ("🔍 Detailed Findings", "findings"),
        ]
        
        self.section_checkboxes = {}
        row, col = 0, 0
        
        for emoji_text, key in sections:
            checkbox = QCheckBox(emoji_text, grid_widget)
            checkbox.setChecked(True)
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    font-size: 12px;
                    font-weight: 500;
                    color: {medical_theme.get_color('text_primary')};
                    spacing: 8px;
                    background: transparent;
                }}
                QCheckBox::indicator {{
                    width: 20px;
                    height: 20px;
                    border: 2px solid {medical_theme.get_color('border_medium')};
                    border-radius: 4px;
                    background: {medical_theme.get_color('bg_primary')};
                }}
                QCheckBox::indicator:checked {{
                    background: {medical_theme.get_color('primary_blue')};
                    border-color: {medical_theme.get_color('primary_blue')};
                    image: url(none);
                }}
                QCheckBox::indicator:hover {{
                    border-color: {medical_theme.get_color('primary_blue')};
                }}
            """)
            grid_layout.addWidget(checkbox, row, col)
            self.section_checkboxes[key] = checkbox
            
            col += 1
            if col > 1:  # 2 columns
                col = 0
                row += 1
        
        layout.addWidget(grid_widget)
        
        # Utility buttons row
        utility_layout = QHBoxLayout()
        utility_layout.setSpacing(8)
        
        # Document Preview button
        preview_btn = AnimatedButton("📄 Preview Document", panel)
        preview_btn.clicked.connect(self._open_document_preview)
        preview_btn.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        utility_layout.addWidget(preview_btn)
        
        # Select All / Deselect All
        select_all_btn = AnimatedButton("☑️ All", panel)
        select_all_btn.clicked.connect(lambda: self._toggle_all_sections(True))
        select_all_btn.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        select_all_btn.setMaximumWidth(80)
        utility_layout.addWidget(select_all_btn)
        
        deselect_all_btn = AnimatedButton("☐ None", panel)
        deselect_all_btn.clicked.connect(lambda: self._toggle_all_sections(False))
        deselect_all_btn.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        deselect_all_btn.setMaximumWidth(80)
        utility_layout.addWidget(deselect_all_btn)
        
        layout.addLayout(utility_layout)
        
        # Export buttons
        export_layout = QHBoxLayout()
        export_layout.setSpacing(8)
        
        export_pdf_btn = AnimatedButton("📄 Export PDF", panel)
        export_pdf_btn.clicked.connect(self._export_report_pdf)
        export_pdf_btn.setStyleSheet(medical_theme.get_button_stylesheet("success"))
        export_layout.addWidget(export_pdf_btn)
        
        export_html_btn = AnimatedButton("🌐 Export HTML", panel)
        export_html_btn.clicked.connect(self._export_report_html)
        export_html_btn.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        export_layout.addWidget(export_html_btn)
        
        layout.addLayout(export_layout)
        
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
        """Create the Settings tab with comprehensive options."""
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("⚙️ Application Settings", tab)
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet(f"color: {medical_theme.get_color('primary_blue')};")
        layout.addWidget(title)
        
        # Settings tabs
        settings_tabs = QTabWidget(tab)
        settings_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 8px;
                background: {medical_theme.get_color('bg_secondary')};
            }}
            QTabBar::tab {{
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                background: {medical_theme.get_color('bg_tertiary')};
                color: {medical_theme.get_color('text_secondary')};
            }}
            QTabBar::tab:selected {{
                background: {medical_theme.get_color('primary_blue')};
                color: white;
            }}
        """)
        
        # User Preferences
        user_prefs_widget = self._create_user_preferences_widget()
        settings_tabs.addTab(user_prefs_widget, "👤 User Preferences")
        
        # Analysis Settings
        analysis_settings_widget = self._create_analysis_settings_widget()
        settings_tabs.addTab(analysis_settings_widget, "📊 Analysis Settings")
        
        # Report Settings
        report_settings_widget = self._create_report_settings_widget()
        settings_tabs.addTab(report_settings_widget, "📄 Report Settings")
        
        # Performance Settings
        perf_widget = self._create_performance_settings_widget()
        settings_tabs.addTab(perf_widget, "⚡ Performance")
        
        # Admin Settings (if admin)
        if self.current_user.is_admin:
            self.settings_editor = SettingsEditorWidget(tab)
            self.settings_editor.save_requested.connect(self.view_model.save_settings)
            settings_tabs.addTab(self.settings_editor, "🔧 Advanced (Admin)")
        
        layout.addWidget(settings_tabs)
        return tab
    
    def _create_user_preferences_widget(self) -> QWidget:
        """Create user preferences settings widget."""
        from PySide6.QtWidgets import QCheckBox
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Theme selection
        theme_section = QWidget()
        theme_section.setStyleSheet(f"""
            QWidget {{
                background: {medical_theme.get_color('bg_primary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        theme_layout = QVBoxLayout(theme_section)
        
        theme_label = QLabel("🎨 Theme Selection", theme_section)
        theme_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        theme_layout.addWidget(theme_label)
        
        theme_buttons = QHBoxLayout()
        light_button = AnimatedButton("☀️ Light Theme", theme_section)
        light_button.clicked.connect(lambda: self._apply_theme("light"))
        light_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        light_button.setMinimumHeight(40)
        theme_buttons.addWidget(light_button)
        
        dark_button = AnimatedButton("🌙 Dark Theme", theme_section)
        dark_button.clicked.connect(lambda: self._apply_theme("dark"))
        dark_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        dark_button.setMinimumHeight(40)
        theme_buttons.addWidget(dark_button)
        
        theme_layout.addLayout(theme_buttons)
        layout.addWidget(theme_section)
        
        # Account settings
        account_section = QWidget()
        account_section.setStyleSheet(f"""
            QWidget {{
                background: {medical_theme.get_color('bg_primary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        account_layout = QVBoxLayout(account_section)
        
        account_label = QLabel("👤 Account Settings", account_section)
        account_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        account_layout.addWidget(account_label)
        
        user_info = QLabel(f"Logged in as: {self.current_user.username}", account_section)
        user_info.setStyleSheet("color: #64748b; padding: 5px;")
        account_layout.addWidget(user_info)
        
        password_button = AnimatedButton("🔒 Change Password", account_section)
        password_button.clicked.connect(self._open_change_password_dialog)
        password_button.setStyleSheet(medical_theme.get_button_stylesheet("secondary"))
        password_button.setMinimumHeight(40)
        account_layout.addWidget(password_button)
        
        layout.addWidget(account_section)
        
        # UI Preferences
        ui_section = QWidget()
        ui_section.setStyleSheet(f"""
            QWidget {{
                background: {medical_theme.get_color('bg_primary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        ui_layout = QVBoxLayout(ui_section)
        
        ui_label = QLabel("🖥️ Interface Preferences", ui_section)
        ui_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        ui_layout.addWidget(ui_label)
        
        show_tooltips = QCheckBox("Show helpful tooltips", ui_section)
        show_tooltips.setChecked(True)
        ui_layout.addWidget(show_tooltips)
        
        auto_save = QCheckBox("Auto-save analysis results", ui_section)
        auto_save.setChecked(True)
        ui_layout.addWidget(auto_save)
        
        show_animations = QCheckBox("Enable button animations", ui_section)
        show_animations.setChecked(True)
        ui_layout.addWidget(show_animations)
        
        layout.addWidget(ui_section)
        
        layout.addStretch()
        return widget
    
    def _create_analysis_settings_widget(self) -> QWidget:
        """Create analysis settings widget."""
        from PySide6.QtWidgets import QCheckBox
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Default Analysis Settings
        section = QWidget()
        section.setStyleSheet(f"""
            QWidget {{
                background: {medical_theme.get_color('bg_primary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        section_layout = QVBoxLayout(section)
        
        title = QLabel("📊 Default Analysis Settings", section)
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        section_layout.addWidget(title)
        
        auto_analyze = QCheckBox("Auto-analyze on document upload", section)
        section_layout.addWidget(auto_analyze)
        
        include_7habits = QCheckBox("Include 7 Habits Framework in reports", section)
        include_7habits.setChecked(True)
        section_layout.addWidget(include_7habits)
        
        include_education = QCheckBox("Include educational resources", section)
        include_education.setChecked(True)
        section_layout.addWidget(include_education)
        
        show_confidence = QCheckBox("Show AI confidence scores", section)
        show_confidence.setChecked(True)
        section_layout.addWidget(show_confidence)
        
        layout.addWidget(section)
        layout.addStretch()
        return widget

    def _create_report_settings_widget(self) -> QWidget:
        """Create report settings widget."""
        from PySide6.QtWidgets import QCheckBox
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Report Content Settings
        section = QWidget()
        section.setStyleSheet(f"""
            QWidget {{
                background: {medical_theme.get_color('bg_primary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        section_layout = QVBoxLayout(section)
        
        title = QLabel("📄 Report Content Settings", section)
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        section_layout.addWidget(title)
        
        include_medicare = QCheckBox("✅ Medicare Guidelines Compliance", section)
        include_medicare.setChecked(True)
        section_layout.addWidget(include_medicare)
        
        include_strengths = QCheckBox("💪 Strengths & Best Practices", section)
        include_strengths.setChecked(True)
        section_layout.addWidget(include_strengths)
        
        include_weaknesses = QCheckBox("⚠️ Weaknesses & Areas for Improvement", section)
        include_weaknesses.setChecked(True)
        section_layout.addWidget(include_weaknesses)
        
        include_suggestions = QCheckBox("💡 Actionable Suggestions", section)
        include_suggestions.setChecked(True)
        section_layout.addWidget(include_suggestions)
        
        include_education_res = QCheckBox("📚 Educational Resources", section)
        include_education_res.setChecked(True)
        section_layout.addWidget(include_education_res)
        
        include_habits = QCheckBox("🎯 7 Habits Framework Integration", section)
        include_habits.setChecked(True)
        section_layout.addWidget(include_habits)
        
        include_score = QCheckBox("📊 Compliance Score & Risk Level", section)
        include_score.setChecked(True)
        section_layout.addWidget(include_score)
        
        include_findings = QCheckBox("🔍 Detailed Findings Analysis", section)
        include_findings.setChecked(True)
        section_layout.addWidget(include_findings)
        
        layout.addWidget(section)
        layout.addStretch()
        return widget

    def _create_performance_settings_widget(self) -> QWidget:
        """Create performance settings widget."""
        from PySide6.QtWidgets import QCheckBox
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        section = QWidget()
        section.setStyleSheet(f"""
            QWidget {{
                background: {medical_theme.get_color('bg_primary')};
                border: 2px solid {medical_theme.get_color('border_light')};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        section_layout = QVBoxLayout(section)
        
        title = QLabel("⚡ Performance Settings", section)
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        section_layout.addWidget(title)
        
        enable_cache = QCheckBox("Enable analysis caching", section)
        enable_cache.setChecked(True)
        section_layout.addWidget(enable_cache)
        
        parallel_processing = QCheckBox("Enable parallel processing", section)
        parallel_processing.setChecked(True)
        section_layout.addWidget(parallel_processing)
        
        auto_cleanup = QCheckBox("Auto-cleanup temporary files", section)
        auto_cleanup.setChecked(True)
        section_layout.addWidget(auto_cleanup)
        
        layout.addWidget(section)
        
        info_label = QLabel("💡 Tip: Enable caching for faster repeated analyses", widget)
        info_label.setStyleSheet("color: #64748b; font-style: italic; padding: 10px;")
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
        """Build status bar with AI indicators, progress, and branding at the bottom."""
        status: QStatusBar = self.statusBar()
        status.showMessage("Ready")
        
        # AI Model Status Indicators (left side of status bar)
        status.addPermanentWidget(self.status_component)
        
        # Add separator
        separator = QLabel(" | ")
        separator.setStyleSheet("color: #94a3b8;")
        status.addPermanentWidget(separator)
        
        # Subtle loading spinner (hidden by default)
        self.loading_spinner = LoadingSpinner(size=20, parent=self)
        self.loading_spinner.hide()
        status.addPermanentWidget(self.loading_spinner)
        
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
        """Build optional dock widgets (Meta Analytics and Performance - hidden by default)."""
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
        """Create floating AI chat button in bottom left corner with subtle animation."""
        self.chat_button = AnimatedButton("💬 Ask AI Assistant", self)
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
            self.run_analysis_button.setEnabled(True)
            return
        except Exception as exc:
            self._selected_file = None
            error_message = f"Could not display preview: {exc}"
            self.file_display.setPlainText(error_message)
            self.statusBar().showMessage(f"Failed to load {file_path.name}", 5000)
            return

        self._selected_file = file_path
        self._cached_preview_content = content
        
        # Show human-readable summary instead of raw content
        file_info = f"""
📄 Document Selected: {file_path.name}
📊 File Size: {len(content)} characters
📁 Location: {file_path.parent}

✅ Ready for analysis!

Click "Run Compliance Analysis" to begin.
        """
        self.file_display.setPlainText(file_info)
        self.statusBar().showMessage(f"✅ Document loaded: {self._selected_file.name}", 3000)
        self.run_analysis_button.setEnabled(True)
        self._update_document_preview()

    def _update_document_preview(self) -> None:
        """Document preview is now handled via popup button - this method is deprecated."""
        pass

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

    def _open_chat_dialog(self, initial_message: str = None) -> None:
        """Open the AI chat dialog with optional initial message."""
        if initial_message:
            initial_context = f"User question: {initial_message}\n\nContext: {self.analysis_summary_browser.toPlainText()}"
        else:
            initial_context = self.analysis_summary_browser.toPlainText() or "Provide a compliance summary."
        dialog = ChatDialog(initial_context, self.auth_token, self)
        dialog.exec()

    def _show_about_dialog(self) -> None:
        QMessageBox.information(self, "About", f"Therapy Compliance Analyzer\nWelcome, {self.current_user.username}!")

    def resizeEvent(self, event) -> None:
        """Handle window resize to reposition floating chat button."""
        super().resizeEvent(event)
        margin = 24
        button_height = self.chat_button.height()
        # Position in BOTTOM LEFT corner
        self.chat_button.move(margin, self.height() - button_height - margin)

__all__ = ["MainApplicationWindow"]


