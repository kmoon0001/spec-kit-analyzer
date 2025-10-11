"""ViewModel for the MainApplicationWindow, handling state and business logic."""
from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import requests
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QMessageBox
from requests.exceptions import HTTPError

from src.config import get_settings
from src.core.analysis_error_handler import error_handler
from src.core.analysis_status_tracker import AnalysisState, status_tracker

# Import diagnostic tools
from src.core.analysis_workflow_logger import workflow_logger
from src.gui.workers.analysis_starter_worker import AnalysisStarterWorker
from src.gui.workers.generic_api_worker import (
    FeedbackWorker,
    GenericApiWorker,
    HealthCheckWorker,
    LogStreamWorker,
    TaskMonitorWorker,
)
from src.gui.workers.single_analysis_polling_worker import SingleAnalysisPollingWorker

logger = logging.getLogger(__name__)
SETTINGS = get_settings()
API_URL = SETTINGS.paths.api_url


class MainViewModel(QObject):
    """ViewModel for the MainApplicationWindow, managing state and business logic."""

    status_message_changed = Signal(str)
    api_status_changed = Signal(str, str)
    task_list_changed = Signal(dict)
    log_message_received = Signal(str)
    settings_loaded = Signal(dict)
    analysis_result_received = Signal(dict)
    rubrics_loaded = Signal(list)
    dashboard_data_loaded = Signal(dict)
    meta_analytics_loaded = Signal(dict)
    show_message_box_signal = Signal(str, str, str, list, str)

    def __init__(self, auth_token: str, parent: QObject | None = None) -> None:
        super().__init__(parent)

        if not auth_token:
            raise ValueError("auth_token cannot be empty or None")

        self.auth_token = auth_token
        self._active_threads: list[QThread] = []
        self._local_tasks: dict[str, Any] = {}
        self._api_tasks: dict[str, Any] = {}

    def update_local_task_status(self, task_id: str, filename: str, status: str, progress: int) -> None:
        """Update the status of a locally managed task and refresh the task list."""
        self._local_tasks[task_id] = {
            "id": task_id,
            "filename": filename,
            "status": status,
            "progress": progress,
            "timestamp": QThread.currentThread(),  # Corrected method
        }
        self._emit_combined_tasks()

    def _emit_combined_tasks(self) -> None:
        """Merge local and API tasks and emit the update signal."""
        combined_tasks = {**self._api_tasks, **self._local_tasks}
        self.task_list_changed.emit(combined_tasks)

    def start_workers(self) -> None:
        self._start_health_check_worker()
        self._start_task_monitor_worker()
        self._start_log_stream_worker()
        self.load_rubrics()
        self.load_dashboard_data()
        try:
            from src.gui.widgets.meta_analytics_widget import MetaAnalyticsWidget

            if MetaAnalyticsWidget:
                self.load_meta_analytics()
        except ImportError:
            pass

    def _run_worker(
        self,
        worker_class,
        on_success: Callable | None = None,
        on_error: Callable | None = None,
        *,
        success_signal: str | None = "success",
        error_signal: str | None = "error",
        auto_stop: bool = True,
        start_slot: str = "run",
        **kwargs: Any) -> None:
        thread = QThread()
        worker = worker_class(**kwargs)
        worker.moveToThread(thread)
        thread._worker_ref = worker

        def connect_signal(signal_name: str | None, callback: Callable | None, should_quit: bool) -> None:
            if not signal_name:
                return
            if not hasattr(worker, signal_name):
                if callback is not None:
                    raise AttributeError(f"{worker_class.__name__} does not expose signal '{signal_name}'") from None
                return
            signal = getattr(worker, signal_name)
            if callback is not None:
                signal.connect(callback)
            if should_quit:
                signal.connect(thread.quit)

        connect_signal(success_signal, on_success, auto_stop)
        connect_signal(error_signal, on_error, auto_stop)

        if hasattr(worker, "finished"):
            worker.finished.connect(thread.quit)

        thread.finished.connect(thread.deleteLater)
        if hasattr(worker, "deleteLater"):
            thread.finished.connect(worker.deleteLater)

        def _cleanup() -> None:
            if hasattr(thread, "_worker_ref"):
                thread._worker_ref = None
            if thread in self._active_threads:
                self._active_threads.remove(thread)

        thread.finished.connect(_cleanup)

        start_callable = getattr(worker, start_slot)
        thread.started.connect(start_callable)

        self._active_threads.append(thread)
        thread.start()

    def _start_health_check_worker(self) -> None:
        def handle_health_check_success(health_data):
            status = "connected" if health_data.get("status") == "healthy" else "error"
            message = health_data.get("message", "API is healthy")
            self.api_status_changed.emit(status, message)
        
        self._run_worker(
            HealthCheckWorker,
            on_success=handle_health_check_success,
            success_signal="success",
            error_signal=None,
            auto_stop=False)

    def _start_task_monitor_worker(self) -> None:
        def handle_success(tasks: dict[str, Any]):
            self._api_tasks = tasks
            self._emit_combined_tasks()

        self._run_worker(
            TaskMonitorWorker,
            on_success=handle_success,
            on_error=lambda msg: self.status_message_changed.emit(f"Task Monitor Error: {msg}"),
            success_signal="tasks_updated",
            auto_stop=False,
            token=self.auth_token)

    def _start_log_stream_worker(self) -> None:
        self._run_worker(
            LogStreamWorker,
            on_success=self.log_message_received.emit,
            on_error=lambda msg: self.status_message_changed.emit(f"Log Stream: {msg}"),
            success_signal="log_received",
            auto_stop=False,
            token=self.auth_token)

    def load_rubrics(self) -> None:
        self._run_worker(
            GenericApiWorker,
            on_success=self.rubrics_loaded.emit,
            on_error=lambda msg: self.status_message_changed.emit(f"Could not load rubrics: {msg}"),
            method="GET",
            endpoint="/rubrics",
            token=self.auth_token)

    def load_dashboard_data(self) -> None:
        self._run_worker(
            GenericApiWorker,
            on_success=self.dashboard_data_loaded.emit,
            on_error=lambda msg: self.status_message_changed.emit(f"Could not load dashboard data: {msg}"),
            method="GET",
            endpoint="/dashboard/statistics",
            token=self.auth_token)

    def load_meta_analytics(self, params: dict[str, Any] | None = None) -> None:
        endpoint = "/meta-analytics/widget_data"
        if params:
            param_str = f"days_back={params.get('days_back', 90)}&discipline={params.get('discipline', '')}"
            endpoint += f"?{param_str}"
        self._run_worker(
            GenericApiWorker,
            on_success=self.meta_analytics_loaded.emit,
            on_error=lambda msg: self.status_message_changed.emit(f"Could not load meta-analytics: {msg}"),
            method="GET",
            endpoint=endpoint,
            token=self.auth_token)

    def start_analysis(self, file_path: str, options: dict) -> None:
        self.status_message_changed.emit(f"Submitting document for analysis: {Path(file_path).name}")
        self._run_worker(
            AnalysisStarterWorker,
            on_success=self._handle_analysis_task_started,
            on_error=lambda msg: self.status_message_changed.emit(f"Analysis failed: {msg}"),
            file_path=file_path,
            data=options,
            token=self.auth_token)

    def _handle_analysis_task_started(self, task_id: str) -> None:
        workflow_logger.log_api_response(200, {"task_id": task_id})
        status_tracker.set_task_id(task_id)
        status_tracker.update_status(AnalysisState.PROCESSING, 20, f"Analysis task created: {task_id[:8]}...")
        self.status_message_changed.emit(f"Analysis running (Task: {task_id[:8]}...)…")
        self._run_worker(
            SingleAnalysisPollingWorker,
            on_success=self._on_analysis_polling_success,
            on_error=self._handle_analysis_error_with_logging,
            task_id=task_id,
            token=self.auth_token)

    def _on_analysis_polling_success(self, result: dict) -> None:
        """Handle successful analysis with comprehensive logging."""
        workflow_logger.log_workflow_completion(True, result)
        status_tracker.complete_analysis(result)
        self.analysis_result_received.emit(result)

    def _handle_analysis_error_with_logging(self, error_msg: str) -> None:
        """Handle analysis error with comprehensive logging and user-friendly messaging."""
        workflow_logger.log_workflow_completion(False, error=error_msg)
        status_tracker.set_error(error_msg)
        analysis_error = error_handler.categorize_and_handle_error(error_msg)
        formatted_message = error_handler.format_error_message(analysis_error, include_technical=False)
        self.show_message_box_signal.emit(
            f"{analysis_error.icon} Analysis Error",
            formatted_message,
            str(QMessageBox.Icon.Warning if analysis_error.severity == "warning" else QMessageBox.Icon.Critical),
            ["🔧 Technical Details", "Ok"],
            error_handler.format_error_message(analysis_error, include_technical=True))

    def load_settings(self) -> None:
        self._run_worker(
            GenericApiWorker,
            on_success=self.settings_loaded.emit,
            on_error=lambda msg: self.status_message_changed.emit(f"Failed to load settings: {msg}"),
            method="GET",
            endpoint="/admin/settings",
            token=self.auth_token)

    def save_settings(self, settings: dict) -> None:
        auth_token = self.auth_token

        class SettingsSaveWorker(QThread):
            success = Signal(str)
            error = Signal(str)

            def run(self) -> None:
                try:
                    response = requests.post(
                        f"{API_URL}/admin/settings",
                        headers={"Authorization": f"Bearer {auth_token}"},
                        json=settings,
                        timeout=10)
                    response.raise_for_status()
                    self.success.emit(response.json().get("message", "Success!"))
                except (requests.RequestException, ValueError, KeyError) as e:
                    self.error.emit(str(e))
                except (ConnectionError, TimeoutError, HTTPError) as e:
                    self.error.emit(f"Unexpected error: {e!s}")

        self._run_worker(
            SettingsSaveWorker,
            on_success=lambda msg: self.status_message_changed.emit(msg),
            on_error=lambda msg: self.status_message_changed.emit(f"Failed to save settings: {msg}"))

    def submit_feedback(self, feedback_data: dict[str, Any]) -> None:
        self._run_worker(
            FeedbackWorker,
            on_success=self.status_message_changed.emit,
            on_error=lambda msg: self.status_message_changed.emit(f"Feedback Error: {msg}"),
            token=self.auth_token,
            feedback_data=feedback_data)

    def stop_all_workers(self) -> None:
        """Stop all worker threads quickly - don't wait too long."""
        logger.debug("Stopping %d worker threads", len(self._active_threads))

        for thread in list(self._active_threads):
            try:
                if thread.isRunning():
                    if hasattr(thread, "_worker_ref") and thread._worker_ref:
                        worker = thread._worker_ref
                        if hasattr(worker, "stop"):
                            worker.stop()

                    thread.quit()

                    if not thread.wait(50):
                        logger.warning("Thread did not quit gracefully, terminating")
                        thread.terminate()
                        thread.wait(50)

            except (RuntimeError, AttributeError):
                pass
            except Exception as e:
                logger.warning("Error stopping thread: %s", e)

        self._active_threads.clear()
        logger.debug("All worker threads stopped")