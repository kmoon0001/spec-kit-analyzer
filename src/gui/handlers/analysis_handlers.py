"""Analysis-related event handlers for the main window."""
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import QMessageBox

from src.core.analysis_diagnostics import diagnostics
from src.core.analysis_error_handler import error_handler
from src.core.analysis_status_tracker import AnalysisState, status_tracker
from src.core.analysis_workflow_logger import workflow_logger

if TYPE_CHECKING:
    from src.gui.main_window import MainApplicationWindow

logger = logging.getLogger(__name__)


class AnalysisHandlers:
    """Handles analysis-related events and operations for compliance checking.

    This class manages the complete analysis workflow including pre-flight validation,
    analysis execution, progress monitoring, and result processing. It integrates with
    the backend analysis services while providing comprehensive error handling and
    user feedback throughout the process.

    The analysis workflow includes:
    1. Pre-flight validation (document, rubric, system health)
    2. Analysis task initiation and monitoring
    3. Progress tracking and user feedback
    4. Result processing and display
    5. Error handling and recovery

    Attributes:
        main_window: Reference to the main application window instance

    Example:
        >>> analysis_handlers = AnalysisHandlers(main_window)
        >>> analysis_handlers.start_analysis()  # Begin compliance analysis
        >>> analysis_handlers.stop_analysis()   # Cancel running analysis

    """

    def __init__(self, main_window: MainApplicationWindow) -> None:
        """Initialize the analysis handlers with a reference to the main window.

        Args:
            main_window: The main application window instance that this handler
                        will operate on. Must have analysis-related UI components
                        including rubric_selector, run_analysis_button, etc.

        Raises:
            TypeError: If main_window is not a valid MainApplicationWindow instance.

        """
        if not hasattr(main_window, "statusBar"):
            raise TypeError("main_window must be a valid MainApplicationWindow instance")
        self.main_window = main_window

    def start_analysis(self) -> None:
        """Start the compliance analysis process with comprehensive validation.

        This method orchestrates the complete analysis workflow, beginning with
        thorough pre-flight validation to ensure all prerequisites are met,
        followed by system diagnostics, and finally initiating the analysis task.

        The analysis process includes:
        1. Document validation (file exists, readable, supported format)
        2. Rubric validation (compliance guidelines selected)
        3. System health checks (API connectivity, analysis services)
        4. Analysis task creation and monitoring setup
        5. UI state management during processing

        Pre-flight Validation:
            - Verifies document is selected and accessible
            - Confirms compliance rubric is chosen
            - Runs system diagnostics to check service health
            - Validates analysis prerequisites are met

        Side Effects:
            - Updates UI button states (disables start, enables stop)
            - Shows progress indicators and status messages
            - Initiates background analysis task
            - Sets up progress monitoring and result handling

        Raises:
            No exceptions are raised directly, but validation failures are
            presented to the user via message boxes and status updates.

        Example:
            >>> analysis_handlers.start_analysis()
            # Validates prerequisites, starts analysis, updates UI

        """
        # Pre-flight checks - Document validation
        if not self.main_window._selected_file:
            QMessageBox.warning(self.main_window, "No Document", "Please select a document before starting the analysis.")
            return

        # Pre-flight checks - Rubric validation
        if not self.main_window.rubric_selector or not self.main_window.rubric_selector.currentData():
            QMessageBox.warning(self.main_window, "No Rubric", "Please select a compliance guideline before analysis.")
            return

        # System health diagnostics
        self.main_window.statusBar().showMessage("🔍 Running pre-analysis diagnostics...", 2000)
        diagnostic_results = diagnostics.run_full_diagnostic()

        # Check for critical system issues that would prevent analysis
        critical_issues = [
            result for result in diagnostic_results.values()
            if result.status.value == "error" and result.component in ["api_connectivity", "analysis_endpoints"]
        ]

        if critical_issues:
            error_messages = [f"• {issue.message}" for issue in critical_issues]
            QMessageBox.critical(
                self.main_window,
                "🚨 Analysis Prerequisites Failed",
                "Cannot start analysis due to critical issues:\n\n" + "\n".join(error_messages) +
                "\n\nPlease resolve these issues and try again.",
            )
            return

        # Validate the selected file
        file_validation = diagnostics.validate_file_format(str(self.main_window._selected_file))
        if file_validation.status.value == "error":
            QMessageBox.warning(
                self.main_window,
                "📄 File Validation Failed",
                f"The selected file cannot be processed:\n\n{file_validation.message}\n\nPlease select a different file.",
            )
            return

        # Start workflow logging and tracking
        rubric_name = self.main_window.rubric_selector.currentText() if self.main_window.rubric_selector else "Unknown"
        session_id = workflow_logger.log_analysis_start(
            str(self.main_window._selected_file),
            rubric_name,
            self.main_window.current_user.username,
        )

        status_tracker.start_tracking(
            session_id,
            str(self.main_window._selected_file),
            rubric_name,
        )

        # Prepare analysis options
        options = {
            "discipline": self.main_window.rubric_selector.currentData() if self.main_window.rubric_selector else "",
            "analysis_mode": "rubric",
            "session_id": session_id,
        }

        # Update UI state
        if self.main_window.run_analysis_button:
            self.main_window.run_analysis_button.setEnabled(False)
        if self.main_window.repeat_analysis_button:
            self.main_window.repeat_analysis_button.setEnabled(False)
        if self.main_window.stop_analysis_button:
            self.main_window.stop_analysis_button.setEnabled(True)  # Enable stop button during analysis
        if self.main_window.view_report_button:
            self.main_window.view_report_button.setEnabled(False)

        # Show loading indicators
        if self.main_window.loading_spinner:
            self.main_window.loading_spinner.start_spinning()
        self.main_window.statusBar().showMessage("⏳ Starting analysis... This may take a moment.", 0)

        # Update status tracker
        status_tracker.update_status(AnalysisState.STARTING, 0, "Submitting analysis request...")

        try:
            # Log the analysis request
            workflow_logger.log_api_request("/analysis/submit", "POST", options)

            # Start the analysis
            self.main_window.view_model.start_analysis(str(self.main_window._selected_file), options)

            # Update status
            status_tracker.update_status(AnalysisState.UPLOADING, 10, "Document uploaded, processing...")

        except (FileNotFoundError, PermissionError, OSError, IOError) as e:
            # Log the error
            workflow_logger.log_workflow_completion(False, error=str(e))
            status_tracker.set_error(f"Failed to start analysis: {e!s}")

            # Reset UI
            if self.main_window.loading_spinner:
                self.main_window.loading_spinner.stop_spinning()
            if self.main_window.run_analysis_button:
                self.main_window.run_analysis_button.setEnabled(True)
            if self.main_window.repeat_analysis_button:
                self.main_window.repeat_analysis_button.setEnabled(True)

            # Use error handler for user-friendly error message
            analysis_error = error_handler.categorize_and_handle_error(str(e))
            formatted_message = error_handler.format_error_message(analysis_error, include_technical=False)

            # Show user-friendly error dialog
            msg = QMessageBox(self.main_window)
            msg.setWindowTitle(f"{analysis_error.icon} Analysis Startup Error")
            msg.setText(formatted_message)
            msg.setIcon(QMessageBox.Icon.Critical if analysis_error.severity == "critical" else QMessageBox.Icon.Warning)

            # Add "Show Technical Details" button
            technical_button = msg.addButton("🔧 Technical Details", QMessageBox.ButtonRole.ActionRole)
            msg.addButton(QMessageBox.StandardButton.Ok)

            msg.exec()

            # Show technical details if requested
            if msg.clickedButton() == technical_button:
                technical_msg = error_handler.format_error_message(analysis_error, include_technical=True)
                QMessageBox.information(self.main_window, "🔧 Technical Details", technical_msg)
            self.main_window.statusBar().showMessage("❌ Analysis failed to start", 5000)

    def repeat_analysis(self) -> None:
        """Repeat analysis on the same document with current settings."""
        if not self.main_window._selected_file:
            QMessageBox.warning(self.main_window, "No document", "No document selected to repeat analysis.")
            return

        self.main_window.statusBar().showMessage("Repeating analysis...", 2000)
        self.start_analysis()

    def stop_analysis(self) -> None:
        """Stop the currently running analysis with user confirmation."""
        # Confirm with user before stopping
        reply = QMessageBox.question(
            self.main_window,
            "⏹️ Stop Analysis",
            "Are you sure you want to stop the current analysis?\n\n"
            "This will cancel the analysis in progress and you'll need to restart it.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Stop the analysis worker if it exists
                if hasattr(self.main_window.view_model, "current_worker") and self.main_window.view_model.current_worker:
                    self.main_window.view_model.current_worker.terminate()

                # Reset UI state
                if self.main_window.loading_spinner:
                    self.main_window.loading_spinner.stop_spinning()
                if self.main_window.run_analysis_button:
                    self.main_window.run_analysis_button.setEnabled(True)
                if self.main_window.repeat_analysis_button:
                    self.main_window.repeat_analysis_button.setEnabled(True)
                if self.main_window.stop_analysis_button:
                    self.main_window.stop_analysis_button.setEnabled(False)

                # Update status
                self.main_window.statusBar().showMessage("⏹️ Analysis stopped by user", 5000)

                # Log the cancellation
                logger.info("Analysis stopped by user request")

            except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
                logger.exception("Error stopping analysis: %s", e)
                QMessageBox.warning(
                    self.main_window,
                    "Stop Analysis Error",
                    f"Could not stop analysis cleanly: {e!s}\n\n"
                    "The analysis may continue in the background.",
                )

    def handle_analysis_success(self, payload: dict[str, Any]) -> None:
        """Handle successful analysis completion with automatic report display."""
        # Hide loading spinner
        if self.main_window.loading_spinner:
            self.main_window.loading_spinner.stop_spinning()

        # Update UI state
        self.main_window.statusBar().showMessage("✅ Analysis Complete - Report displayed automatically", 5000)
        if self.main_window.run_analysis_button:
            self.main_window.run_analysis_button.setEnabled(True)
        if self.main_window.repeat_analysis_button:
            self.main_window.repeat_analysis_button.setEnabled(True)
        if self.main_window.stop_analysis_button:
            self.main_window.stop_analysis_button.setEnabled(False)  # Disable stop button when analysis complete
        if self.main_window.view_report_button:
            self.main_window.view_report_button.setEnabled(True)
        self.main_window._current_payload = payload

        # Display human-readable summary in results tab
        analysis = payload.get("analysis", {})
        doc_name = self.main_window._selected_file.name if self.main_window._selected_file else "Document"

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

The detailed report has been automatically displayed in a popup window.

You can also:
- Click "🔄 Repeat" to run analysis again
- Click "📊 View Report" to see the report again
- Click "📄 Export PDF" or "🌐 Export HTML" to save the report
        """

        if self.main_window.analysis_summary_browser:
            self.main_window.analysis_summary_browser.setPlainText(summary_text)
        if self.main_window.detailed_results_browser:
            self.main_window.detailed_results_browser.setPlainText(json.dumps(payload, indent=2))

        # AUTOMATICALLY DISPLAY THE ENHANCED REPORT POPUP (Best Practice: Immediate Results)
        try:
            # Display the enhanced report popup immediately
            self.main_window._open_report_popup()

        except (RuntimeError, AttributeError) as e:
            # Fallback: Log error but don't break the workflow
            logger.warning("Warning: Could not auto-display report popup: %s", e)
            self.main_window.statusBar().showMessage("✅ Analysis Complete - Click 'View Report' to see results", 5000)

        # Refresh dashboard after analysis
        self.main_window.view_model.load_dashboard_data()

    def handle_analysis_error(self, message: str) -> None:
        """Handles analysis errors by surfacing the status."""
        self.main_window.statusBar().showMessage(f"Analysis failed: {message}", 5000)

    def on_strictness_selected_with_description(self, index: int) -> None:
        """Handle strictness level selection with description update."""
        # Uncheck all other buttons
        for i, btn in enumerate(self.main_window.strictness_buttons):
            btn.setChecked(i == index)

        # Update description
        self.update_strictness_description(index)

        # Update status
        level = self.main_window.strictness_levels[index][0]
        self.main_window.statusBar().showMessage(f"Review strictness set to: {level}", 3000)

    def update_strictness_description(self, index: int) -> None:
        """Update the strictness description based on selected level."""
        if hasattr(self.main_window, "strictness_description") and hasattr(self.main_window, "strictness_levels"):
            level, emoji, info = self.main_window.strictness_levels[index]

            description_html = f"""
            <div style='font-family: Segoe UI; line-height: 1.5;'>
                <h3 style='color: #1d4ed8; margin-top: 0; margin-bottom: 10px;'>{emoji} {level} Analysis</h3>
                <p style='color: #475569; margin-bottom: 15px; font-weight: 500;'>{info['description']}</p>

                <div style='background: #f1f5f9; padding: 12px; border-radius: 6px; margin-bottom: 12px;'>
                    <h4 style='color: #334155; margin: 0 0 8px 0; font-size: 13px;'>Analysis Details:</h4>
                    <div style='color: #64748b; font-size: 12px; white-space: pre-line;'>{info['details']}</div>
                </div>

                <div style='color: #059669; font-weight: 500; font-size: 12px;'>{info['use_case']}</div>
            </div>
            """

            self.main_window.strictness_description.setText(description_html)

    def on_ai_models_ready(self) -> None:
        """Called when AI models are loaded and ready."""
        if self.main_window.status_component:
            self.main_window.status_component.set_all_ready()
            status_text = self.main_window.status_component.get_status_text()
        else:
            status_text = "AI Models Ready"
        self.main_window.statusBar().showMessage(f"✅ {status_text}", 5000)
