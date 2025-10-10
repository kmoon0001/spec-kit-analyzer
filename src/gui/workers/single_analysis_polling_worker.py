import logging
import time
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

            try:
                # Log polling attempt
                workflow_logger.log_polling_attempt(self.task_id, attempts)

                headers = {}
                if self.token:
                    headers["Authorization"] = f"Bearer {self.token}"
                
                response = requests.get(
                    f"{API_URL}/analysis/status/{self.task_id}",
                    headers=headers,
                    timeout=15)
                response.raise_for_status()

                # Log API response
                workflow_logger.log_api_response(response.status_code, response.json() if response.content else None)

                if response.headers.get("Content-Type", "").startswith("text/html"):
                    logger.warning("Received HTML response instead of JSON for task %s", self.task_id)
                    self.success.emit(response.text)
                    self.finished.emit()
                    return

                status_data: dict[str, Any] = response.json()
                logger.info("Polling response: %s", status_data)
                status = status_data.get("status", "unknown")
                progress = status_data.get("progress", 0)

                # Log detailed polling status
                workflow_logger.log_polling_attempt(self.task_id, attempts, status, progress)

                if status == "processing":
                    reported_progress = int(progress if progress else (attempts * 100 // max_attempts))

                    # Update status tracker
                    status_tracker.update_status(
                        AnalysisState.PROCESSING,
                        reported_progress,
                        f"Processing... ({reported_progress}%)")

                    self.progress.emit(max(0, min(100, reported_progress)))
                    logger.debug("Task %s processing: {reported_progress}%", self.task_id)

                elif status == "failed":
                    error_msg = status_data.get("error", "Unknown error during analysis.")
                    logger.error("Task %s failed: {error_msg}", self.task_id)

                    # Update status tracker
                    status_tracker.set_error(error_msg)

                    self.error.emit(error_msg)
                    self.finished.emit()
                    return

                elif status == "completed":
                    result = status_data.get("result")
                    logger.info("Task %s completed successfully", self.task_id)

                    # Update status tracker
                    status_tracker.complete_analysis(result)

                    self.success.emit(result)
                    self.finished.emit()
                    return

                elif status == "pending":
                    logger.debug("Task %s still pending (attempt {attempts})", self.task_id)
                    status_tracker.update_status(
                        AnalysisState.POLLING,
                        5,
                        "Analysis queued, waiting to start...")
                else:
                    logger.warning("Unknown status '%s' for task {self.task_id}", status)
                    status_tracker.update_status(
                        AnalysisState.POLLING,
                        attempts * 100 // max_attempts,
                        f"Unknown status: {status}")

            except requests.RequestException as exc:
                logger.exception("Network error polling task %s: {exc}", self.task_id)
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
                return

            except Exception as exc:
                logger.exception("Unexpected error polling task %s: {exc}", self.task_id)
                workflow_logger.log_api_response(0, error=str(exc))
                self.error.emit(f"An unexpected error occurred while checking analysis status: {exc}")
                self.finished.emit()
                return

            time.sleep(poll_interval)

        # Handle timeout
        if attempts >= max_attempts:
            timeout_msg = f"Analysis timed out after {max_attempts * poll_interval} seconds ({max_attempts} attempts)"
            logger.error("Task %s timed out", self.task_id)
            workflow_logger.log_workflow_timeout(max_attempts * poll_interval)
            status_tracker.update_status(AnalysisState.TIMEOUT, 100, "Analysis timed out")
            self.error.emit(timeout_msg)

        self.finished.emit()
