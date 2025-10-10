"""ViewModel for the MainApplicationWindow, handling state and business logic."""
from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import requests
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QMessageBox

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
    """
    ViewModel for the MainApplicationWindow, managing state and business logic.

    This class implements the MVVM (Model-View-ViewModel) pattern, serving as the
    intermediary between the UI (View) and the business logic/data (Model). It
    handles all state management, API communications, background task coordination,
    and provides a clean interface for the UI to interact with backend services.

    Key Responsibilities:
    - State management for the main application window
    - API communication with the FastAPI backend
    - Background task coordination and monitoring
    - Data loading and caching for UI components
    - Error handling and user feedback coordination
    - Thread management for non-blocking operations

    Signals:
        status_message_changed: Emitted when status bar message should update
        api_status_changed: Emitted when API connectivity status changes
        task_list_changed: Emitted when background task list updates
        log_message_received: Emitted when new log messages are available
        settings_loaded: Emitted when application settings are loaded
        analysis_result_received: Emitted when analysis results are ready
        rubrics_loaded: Emitted when compliance rubrics are loaded
        dashboard_data_loaded: Emitted when dashboard data is ready
        meta_analytics_loaded: Emitted when analytics data is loaded
        show_message_box_signal: Emitted to request message box display

    Example:
        >>> view_model = MainViewModel(auth_token="jwt_token")
        >>> view_model.start_workers()  # Initialize background services
        >>> view_model.start_analysis(document_path, rubric_id)  # Begin analysis
    """
    # UI State Management Signals
    status_message_changed = Signal(str)  # Status bar message updates
    api_status_changed = Signal(str, str)  # API connectivity status (status, message)
    task_list_changed = Signal(dict)  # Background task list updates
    log_message_received = Signal(str)  # Application log messages

    # Data Loading Signals
    settings_loaded = Signal(dict)  # Application settings loaded
    analysis_result_received = Signal(dict)  # Analysis results ready
    rubrics_loaded = Signal(list)  # Compliance rubrics loaded
    dashboard_data_loaded = Signal(dict)  # Dashboard data ready
    meta_analytics_loaded = Signal(dict)  # Analytics data loaded

    # User Interaction Signals
    show_message_box_signal = Signal(str, str, str, list, str)  # Message box requests

    def __init__(self, auth_token: str, parent: QObject | None = None) -> None:
        """
        Initialize the MainViewModel with authentication and state management.

        Args:
            auth_token: JWT authentication token for API communications.
                       Must be a valid token obtained from the authentication system.
            parent: Optional parent QObject for Qt object hierarchy management.
                   Defaults to None for top-level object.

        Raises:
            ValueError: If auth_token is empty or None.

        Side Effects:
            - Initializes the Qt object hierarchy
            - Sets up authentication for API calls
            - Initializes empty thread tracking list
            - Prepares signal/slot connections
        """
        super().__init__(parent)

        if not auth_token:
            raise ValueError("auth_token cannot be empty or None")

        self.auth_token = auth_token
        self._active_threads: list[QThread] = []  # Track background threads for cleanup

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
        **kwargs: Any,
    ) -> None:
        thread = QThread()
        worker = worker_class(**kwargs)
        worker.moveToThread(thread)
        thread._worker_ref = worker

        def connect_signal(signal_name: str | None, callback: Callable | None, should_quit: bool) -> None:
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

    def load_meta_analytics(self, params: dict[str, Any] | None = None) -> None:
        endpoint = "/meta-analytics/widget_data"
        if params:
            param_str = f"days_back={params.get('days_back', 90)}&discipline={params.get('discipline', '')}"
            endpoint += f"?{param_str}"
        self._run_worker(GenericApiWorker, on_success=self.meta_analytics_loaded.emit, on_error=lambda msg: self.status_message_changed.emit(f"Could not load meta-analytics: {msg}"), endpoint=endpoint, token=self.auth_token)

    def start_analysis(self, file_path: str, options: dict) -> None:
        self.status_message_changed.emit(f"Submitting document for analysis: {Path(file_path).name}")
        self._run_worker(AnalysisStarterWorker, on_success=self._handle_analysis_task_started, on_error=lambda msg: self.status_message_changed.emit(f"Analysis failed: {msg}"), file_path=file_path, data=options, token=self.auth_token)

    def _handle_analysis_task_started(self, task_id: str) -> None:
        # Log successful task creation
        workflow_logger.log_api_response(200, {"task_id": task_id})

        # Update status tracker with task ID
        status_tracker.set_task_id(task_id)
        status_tracker.update_status(AnalysisState.PROCESSING, 20, f"Analysis task created: {task_id[:8]}...")

        self.status_message_changed.emit(f"Analysis running (Task: {task_id[:8]}...)…")

        # Start polling for results
        self._run_worker(
            SingleAnalysisPollingWorker,
            on_success=self._on_analysis_polling_success,
            on_error=self._handle_analysis_error_with_logging,
            task_id=task_id,
        )

    def _on_analysis_polling_success(self, result: dict) -> None:
        """Handle successful analysis with comprehensive logging."""
        # Log successful completion
        workflow_logger.log_workflow_completion(True, result)
        status_tracker.complete_analysis(result)

        # Emit signal for the view to handle
        self.analysis_result_received.emit(result)

    def _handle_analysis_error_with_logging(self, error_msg: str) -> None:
        """Handle analysis error with comprehensive logging and user-friendly messaging."""
        # Log the error
        workflow_logger.log_workflow_completion(False, error=error_msg)
        status_tracker.set_error(error_msg)

        # Process error through error handler for better user experience
        analysis_error = error_handler.categorize_and_handle_error(error_msg)
        formatted_message = error_handler.format_error_message(analysis_error, include_technical=False)

        # Emit signal for the view to show the message box
        self.show_message_box_signal.emit(
            f"{analysis_error.icon} Analysis Error",
            formatted_message,
            str(QMessageBox.Icon.Warning if analysis_error.severity == "warning" else QMessageBox.Icon.Critical),
            ["🔧 Technical Details", "Ok"],
            error_handler.format_error_message(analysis_error, include_technical=True)
        )

    def load_settings(self) -> None:
        self._run_worker(GenericApiWorker, on_success=self.settings_loaded.emit, on_error=lambda msg: self.status_message_changed.emit(f"Failed to load settings: {msg}"), endpoint="/admin/settings", token=self.auth_token)

    def save_settings(self, settings: dict) -> None:
        auth_token = self.auth_token  # Capture in local scope

        class SettingsSaveWorker(QThread):
            success = Signal(str)
            error = Signal(str)
            def run(self) -> None:
                try:
                    response = requests.post(f"{API_URL}/admin/settings", headers={"Authorization": f"Bearer {auth_token}"}, json=settings, timeout=10)
                    response.raise_for_status()
                    self.success.emit(response.json().get("message", "Success!"))
                except (requests.RequestException, ValueError, KeyError) as e:
                    self.error.emit(str(e))
                except Exception as e:
                    self.error.emit(f"Unexpected error: {str(e)}")
        self._run_worker(SettingsSaveWorker, on_success=lambda msg: self.status_message_changed.emit(msg), on_error=lambda msg: self.status_message_changed.emit(f"Failed to save settings: {msg}"))

    def submit_feedback(self, feedback_data: dict[str, Any]) -> None:
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
