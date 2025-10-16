import json
import logging
import uuid
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QMessageBox

from src.core.analysis_service import AnalysisService
from src.gui.workers.analysis_worker import AnalysisWorker

if TYPE_CHECKING:
    from src.gui.main_window import MainApplicationWindow

logger = logging.getLogger(__name__)


class AnalysisHandlers:
    """Handles analysis-related events and operations for compliance checking."""

    def __init__(self, main_window: "MainApplicationWindow") -> None:
        """Initialize the analysis handlers."""
        self.main_window = main_window
        self.analysis_service = AnalysisService()
        self.current_worker: QThread | None = None
        self.worker_obj: AnalysisWorker | None = None
        self.current_task_id: str | None = None

    def start_analysis(self) -> None:
        """Start the compliance analysis process using a local worker thread."""
        if not self.main_window._selected_file:
            QMessageBox.warning(self.main_window, "No Document", "Please select a document.")
            return

        if not self.main_window.rubric_selector or not self.main_window.rubric_selector.currentData():
            QMessageBox.warning(self.main_window, "No Rubric", "Please select a compliance guideline.")
            return

        self._update_ui_for_analysis_start()

        file_path = str(self.main_window._selected_file)
        discipline = self.main_window.rubric_selector.currentData()
        self.current_task_id = f"local-{uuid.uuid4().hex[:8]}"

        self.main_window.view_model.update_local_task_status(
            self.current_task_id, self.main_window._selected_file.name, "Starting", 5
        )

        self.current_worker = QThread()
        self.worker_obj = AnalysisWorker(file_path, discipline, self.analysis_service)
        self.worker_obj.moveToThread(self.current_worker)

        self.worker_obj.progress_updated.connect(self._handle_progress_update)
        self.worker_obj.status_updated.connect(self.main_window.statusBar().showMessage)
        self.worker_obj.analysis_completed.connect(self.handle_analysis_success)
        self.worker_obj.analysis_failed.connect(self.handle_analysis_error)
        self.current_worker.started.connect(self.worker_obj.run)
        self.worker_obj.finished.connect(self.current_worker.quit)
        self.worker_obj.finished.connect(self.worker_obj.deleteLater)
        self.current_worker.finished.connect(self.current_worker.deleteLater)

        self.current_worker.start()

    def _handle_progress_update(self, progress: int):
        self.main_window.show_progress(progress)
        if self.current_task_id and self.main_window._selected_file:
            self.main_window.view_model.update_local_task_status(
                self.current_task_id, self.main_window._selected_file.name, "Processing", progress
            )

    def _update_ui_for_analysis_start(self):
        if self.main_window.run_analysis_button:
            self.main_window.run_analysis_button.setEnabled(False)
        if self.main_window.repeat_analysis_button:
            self.main_window.repeat_analysis_button.setEnabled(False)
        if self.main_window.stop_analysis_button:
            self.main_window.stop_analysis_button.setEnabled(True)

        self.main_window.show_progress(5, "Initializing...")
        self.main_window.statusBar().showMessage("Starting local analysis...")

    def repeat_analysis(self) -> None:
        """Repeat analysis on the same document with current settings."""
        if not self.main_window._selected_file:
            QMessageBox.warning(self.main_window, "No document", "No document selected to repeat analysis.")
            return
        self.main_window.statusBar().showMessage("Repeating analysis...", 2000)
        self.start_analysis()

    def stop_analysis(self) -> None:
        """Stop the currently running analysis."""
        if self.current_worker and self.current_worker.isRunning():
            reply = QMessageBox.question(
                self.main_window,
                "Stop Analysis",
                "Are you sure you want to stop the current analysis?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                if self.current_task_id and self.main_window._selected_file:
                    self.main_window.view_model.update_local_task_status(
                        self.current_task_id, self.main_window._selected_file.name, "Cancelled", 0
                    )
                self.current_worker.quit()
                self.current_worker.wait(5000)
                if self.current_worker.isRunning():
                    self.current_worker.terminate()
                    logger.warning("Analysis thread terminated forcefully.")
                self._reset_ui_after_stop("Analysis stopped by user.")

    def _reset_ui_after_stop(self, message: str):
        self.main_window.hide_progress()
        if self.main_window.run_analysis_button:
            self.main_window.run_analysis_button.setEnabled(True)
        if self.main_window.repeat_analysis_button:
            self.main_window.repeat_analysis_button.setEnabled(True)
        if self.main_window.stop_analysis_button:
            self.main_window.stop_analysis_button.setEnabled(False)
        self.main_window.statusBar().showMessage(message, 5000)
        self.current_worker = None
        self.worker_obj = None
        self.current_task_id = None

    def handle_analysis_success(self, payload: dict[str, Any]) -> None:
        """Handle successful analysis completion and update the dashboard."""
        if self.current_task_id and self.main_window._selected_file:
            self.main_window.view_model.update_local_task_status(
                self.current_task_id, self.main_window._selected_file.name, "Completed", 100
            )

        self._reset_ui_after_stop("Analysis complete.")
        if self.main_window.view_report_button:
            self.main_window.view_report_button.setEnabled(True)
        self.main_window._current_payload = payload

        analysis = payload.get("analysis", {})
        doc_name = self.main_window._selected_file.name if self.main_window._selected_file else "Document"
        summary_text = f"""
ANALYSIS COMPLETE
================
Document: {doc_name}
Compliance Score: {analysis.get("compliance_score", "N/A")}%
Total Findings: {len(analysis.get("findings", []))}

Click 'View Report' to see the detailed results.
        """
        if self.main_window.analysis_summary_browser:
            self.main_window.analysis_summary_browser.setPlainText(summary_text)
        if self.main_window.detailed_results_browser:
            self.main_window.detailed_results_browser.setPlainText(json.dumps(payload, indent=2))

        self._update_dashboard_data(analysis)

        self.main_window._open_report_popup()

    def _update_dashboard_data(self, analysis_result: dict[str, Any]) -> None:
        """Construct dashboard data from analysis and emit signal."""
        score = analysis_result.get("compliance_score", 0.0)
        findings = analysis_result.get("findings", [])

        categories = {}
        for finding in findings:
            category = finding.get("category", "General")
            if category not in categories:
                categories[category] = []
            categories[category].append(finding.get("severity", 1))

        category_scores = {k: 100 - (sum(v) * 10) for k, v in categories.items()}

        dashboard_data = {
            "total_documents_analyzed": 1,
            "overall_compliance_score": score,
            "compliance_by_category": category_scores,
        }
        self.main_window.view_model.dashboard_data_loaded.emit(dashboard_data)

    def handle_analysis_error(self, message: str) -> None:
        """Handles analysis errors by showing a message box and resetting the UI."""
        logger.error(f"Analysis failed with message: {message}")
        if self.current_task_id and self.main_window._selected_file:
            self.main_window.view_model.update_local_task_status(
                self.current_task_id, self.main_window._selected_file.name, "Error", 100
            )
        self._reset_ui_after_stop(f"Analysis failed: {message}")
        QMessageBox.critical(
            self.main_window,
            "Analysis Error",
            f"The analysis could not be completed:\n\n{message}\n\nPlease check the logs for more details.",
        )

    def on_strictness_selected_with_description(self, index: int) -> None:
        """Handle strictness level selection with description update."""
        for i, btn in enumerate(self.main_window.strictness_buttons):
            btn.setChecked(i == index)

        self.update_strictness_description(index)

        level = self.main_window.strictness_levels[index][0]
        self.main_window.statusBar().showMessage(f"Review strictness set to: {level}", 3000)

    def update_strictness_description(self, index: int) -> None:
        """Update the strictness description based on selected level."""
        if hasattr(self.main_window, "strictness_description") and hasattr(self.main_window, "strictness_levels"):
            level, emoji, info = self.main_window.strictness_levels[index]

            description_html = f"""
            <div style='font-family: Segoe UI; line-height: 1.5;'>
                <h3 style='color: #1d4ed8; margin-top: 0; margin-bottom: 10px;'>{emoji} {level} Analysis</h3>
                <p style='color: #475569; margin-bottom: 15px; font-weight: 500;'>{info["description"]}</p>

                <div style='background: #f1f5f9; padding: 12px; border-radius: 6px; margin-bottom: 12px;'>
                    <h4 style='color: #334155; margin: 0 0 8px 0; font-size: 13px;'>Analysis Details:</h4>
                    <div style='color: #64748b; font-size: 12px; white-space: pre-line;'>{info["details"]}</div>
                </div>

                <div style='color: #059669; font-weight: 500; font-size: 12px;'>{info["use_case"]}</div>
            </div>
            """

            self.main_window.strictness_description.setText(description_html)

    def on_ai_models_ready(self) -> None:
        """Called when all AI models are confirmed to be loaded and ready."""
        if self.main_window.run_analysis_button:
            self.main_window.run_analysis_button.setEnabled(True)

        self.main_window.statusBar().showMessage("All AI models are ready. You can now start the analysis.", 5000)
