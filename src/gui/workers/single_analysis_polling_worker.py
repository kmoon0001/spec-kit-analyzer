import logging
from typing import Any

import requests
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal as Signal

from src.config import get_settings
from src.core.analysis_status_tracker import AnalysisState, status_tracker
from src.core.analysis_workflow_logger import workflow_logger

settings = get_settings()
API_URL = settings.paths.api_url


class SingleAnalysisPollingWorker(QObject):
    finished = Signal()  # type: ignore[attr-defined]
    error = Signal(str)  # type: ignore[attr-defined]
    success = Signal(object)  # type: ignore[attr-defined]
    progress = Signal(int)  # type: ignore[attr-defined]

    def __init__(self, task_id: str, token: str = None):
        super().__init__()
        self.task_id = task_id
        self.token = token
        self.is_running = True

    def stop(self) -> None:
        self.is_running = False

    def run(self):
        """Poll the API for the result of the single analysis task."""
        poll_interval = 3  # seconds
        max_attempts = 400  # 20 minutes (3 * 400 = 1200 seconds)
        attempts = 0

        logger = logging.getLogger(__name__)
        logger.info("Starting polling for task: %s", self.task_id)

        while self.is_running and attempts < max_attempts:
            attempts += 1
            logger.debug("Polling attempt %d for task %s. is_running: %s", attempts, self.task_id, self.is_running)

            try:
                # Log polling attempt
                workflow_logger.log_polling_attempt(self.task_id, attempts)

                headers = {}
                if self.token:
                    headers["Authorization"] = f"Bearer {self.token}"

                logger.debug("Sending status request to %s/analysis/status/%s", API_URL, self.task_id)
                response = requests.get(f"{API_URL}/analysis/status/{self.task_id}", headers=headers, timeout=15)
                response.raise_for_status()

                # Log API response
                workflow_logger.log_api_response(response.status_code, response.json() if response.content else None)

                if response.headers.get("Content-Type", "").startswith("text/html"):
                    logger.warning("Received HTML response instead of JSON for task %s", self.task_id)
                    self.success.emit(response.text)
                    self.finished.emit()
                    logger.debug("SingleAnalysisPollingWorker run finished (HTML response).")
                    return

                status_data: dict[str, Any] = response.json()
                logger.info("Polling response for task %s: %s", self.task_id, status_data)
                status = status_data.get("status", "unknown")
                progress = status_data.get("progress", 0)  # Get actual progress from API
                status_message = status_data.get("status_message", "")  # Get actual status message from API

                # Log detailed polling status
                workflow_logger.log_polling_attempt(self.task_id, attempts, status, progress, status_message)

                if status == "processing":
                    # Use actual progress from API, no longer estimate
                    reported_progress = int(progress)

                    # Update status tracker with actual status message
                    status_tracker.update_status(
                        AnalysisState.PROCESSING,
                        reported_progress,
                        status_message if status_message else f"Processing... ({reported_progress}%)",
                    )

                    self.progress.emit(max(0, min(100, reported_progress)))
                    logger.debug("Task %s processing: %d%% - %s", self.task_id, reported_progress, status_message)

                elif status == "failed":
                    error_msg = status_data.get("error", "Unknown error during analysis.")
                    # Use actual status message for error
                    status_message = status_data.get("status_message", error_msg)
                    logger.error("Task %s failed: %s", self.task_id, status_message)

                    # Update status tracker
                    status_tracker.set_error(status_message)

                    self.error.emit(error_msg)
                    self.finished.emit()
                    logger.debug("SingleAnalysisPollingWorker run finished (failed).")
                    return

                elif status == "completed":
                    result = status_data.get("result")
                    # Use actual status message for completion
                    status_message = status_data.get("status_message", "Analysis completed successfully.")
                    logger.info("Task %s completed successfully: %s", self.task_id, status_message)

                    # Update status tracker
                    status_tracker.complete_analysis(result)

                    self.success.emit(result)
                    self.finished.emit()
                    logger.debug("SingleAnalysisPollingWorker run finished (completed).")
                    return

                elif status == "pending":
                    # Use actual status message for pending
                    status_message = status_data.get("status_message", "Analysis queued, waiting to start...")
                    logger.debug("Task %s still pending (attempt %d): %s", self.task_id, attempts, status_message)
                    status_tracker.update_status(AnalysisState.POLLING, 5, status_message)
                else:
                    # Use actual status message for unknown status
                    status_message = status_data.get("status_message", f"Unknown status: {status}")
                    logger.warning("Unknown status '%s' for task %s: %s", status, self.task_id, status_message)
                    status_tracker.update_status(AnalysisState.POLLING, progress, status_message)

            except requests.RequestException as exc:
                logger.exception("Network error polling task %s: %s", self.task_id, exc)
                workflow_logger.log_api_response(0, error=str(exc))

                # For connection errors, provide more specific guidance
                if "Connection refused" in str(exc):
                    error_msg = "Cannot connect to analysis service. Please check if the API server is running."
                elif "timeout" in str(exc).lower():
                    error_msg = "Request timed out while checking analysis status. The server may be overloaded."
                else:
                    error_msg = f"Network error while checking analysis status: {exc}"

                self.error.emit(error_msg)
                self.finished.emit()
                logger.debug("SingleAnalysisPollingWorker run finished (network error).")
                return

            except Exception as exc:
                logger.exception("Unexpected error polling task %s: %s", self.task_id, exc)
                workflow_logger.log_api_response(0, error=str(exc))
                self.error.emit(f"An unexpected error occurred while checking analysis status: {exc}")
                self.finished.emit()
                logger.debug("SingleAnalysisPollingWorker run finished (unexpected error).")
                return

            # Replace long sleep with shorter, responsive sleeps
            for _ in range(int(poll_interval * 10)):
                if not self.is_running:
                    logger.debug(
                        "SingleAnalysisPollingWorker stopping during responsive sleep for task %s", self.task_id
                    )
                    break
                self.msleep(100)

        # Handle timeout
        if attempts >= max_attempts:
            timeout_msg = f"Analysis timed out after {max_attempts * poll_interval} seconds ({max_attempts} attempts)"
            logger.error("Task %s timed out", self.task_id)
            workflow_logger.log_workflow_timeout(max_attempts * poll_interval)
            status_tracker.update_status(AnalysisState.TIMEOUT, 100, "Analysis timed out")
            self.error.emit(timeout_msg)

        logger.debug("SingleAnalysisPollingWorker run finished (timeout or loop end) for task %s.", self.task_id)
        self.finished.emit()
