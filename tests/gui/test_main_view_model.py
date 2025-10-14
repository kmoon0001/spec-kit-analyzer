"""Tests for the MainViewModel class."""

from unittest.mock import Mock, patch

import pytest

# Note: PySide6 imports may need proper Qt testing environment setup
try:
    from PySide6.QtWidgets import QApplication

    from src.gui.view_models.main_view_model import MainViewModel

    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False


@pytest.fixture
def mock_app():
    """Create a mock QApplication for testing."""
    if not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 not available")

    if not QApplication.instance():
        app = QApplication([])
        yield app
        app.quit()
    else:
        yield QApplication.instance()


@pytest.fixture
def view_model(mock_app):
    """Create a MainViewModel instance for testing."""
    return MainViewModel("test_token")


@pytest.mark.skipif(not PYSIDE6_AVAILABLE, reason="PySide6 not available")
class TestMainViewModel:
    """Test cases for MainViewModel."""

    def test_initialization(self, view_model):
        """Test that MainViewModel initializes correctly."""
        assert view_model.auth_token == "test_token"
        assert isinstance(view_model._active_threads, list)
        assert len(view_model._active_threads) == 0

    def test_signals_exist(self, view_model):
        """Test that all required signals are defined."""
        required_signals = [
            "status_message_changed",
            "api_status_changed",
            "task_list_changed",
            "log_message_received",
            "settings_loaded",
            "analysis_result_received",
            "rubrics_loaded",
            "dashboard_data_loaded",
            "meta_analytics_loaded",
            "show_message_box_signal",
        ]

        for signal_name in required_signals:
            assert hasattr(view_model, signal_name)

    @patch("src.gui.view_models.main_view_model.HealthCheckWorker")
    @patch("src.gui.view_models.main_view_model.TaskMonitorWorker")
    @patch("src.gui.view_models.main_view_model.LogStreamWorker")
    def test_start_workers(self, mock_log_worker, mock_task_worker, mock_health_worker, view_model):
        """Test that start_workers initializes all required workers."""
        with patch.object(view_model, "_run_worker") as mock_run_worker:
            with patch.object(view_model, "load_rubrics") as mock_load_rubrics:
                with patch.object(view_model, "load_dashboard_data") as mock_load_dashboard:
                    view_model.start_workers()

                    # Should call _run_worker for health check, task monitor, and log stream
                    assert mock_run_worker.call_count >= 3
                    mock_load_rubrics.assert_called_once()
                    mock_load_dashboard.assert_called_once()

    def test_run_worker_creates_thread(self, view_model):
        """Test that _run_worker creates and manages threads correctly."""
        mock_worker_class = Mock()
        mock_worker = Mock()
        mock_worker_class.return_value = mock_worker

        with patch("src.gui.view_models.main_view_model.QThread") as mock_thread_class:
            mock_thread = Mock()
            mock_thread_class.return_value = mock_thread

            view_model._run_worker(mock_worker_class, test_param="test_value")

            # Verify thread was created and worker was moved to it
            mock_thread_class.assert_called_once()
            mock_worker.moveToThread.assert_called_once_with(mock_thread)
            mock_thread.start.assert_called_once()

    def test_load_rubrics(self, view_model):
        """Test that load_rubrics calls the correct API endpoint."""
        with patch.object(view_model, "_run_worker") as mock_run_worker:
            view_model.load_rubrics()

            mock_run_worker.assert_called_once()
            call_args = mock_run_worker.call_args
            assert "endpoint" in call_args.kwargs
            assert call_args.kwargs["endpoint"] == "/rubrics"
            assert call_args.kwargs["token"] == "test_token"

    def test_load_dashboard_data(self, view_model):
        """Test that load_dashboard_data calls the correct API endpoint."""
        with patch.object(view_model, "_run_worker") as mock_run_worker:
            view_model.load_dashboard_data()

            mock_run_worker.assert_called_once()
            call_args = mock_run_worker.call_args
            assert "endpoint" in call_args.kwargs
            assert call_args.kwargs["endpoint"] == "/dashboard/statistics"

    def test_start_analysis(self, view_model):
        """Test that start_analysis initiates analysis workflow."""
        test_file_path = "/test/path/document.pdf"
        test_options = {"discipline": "pt", "analysis_mode": "rubric"}

        with patch.object(view_model, "_run_worker") as mock_run_worker:
            view_model.start_analysis(test_file_path, test_options)

            mock_run_worker.assert_called_once()
            call_args = mock_run_worker.call_args
            assert call_args.kwargs["file_path"] == test_file_path
            assert call_args.kwargs["data"] == test_options

    @patch("src.gui.view_models.main_view_model.workflow_logger")
    @patch("src.gui.view_models.main_view_model.status_tracker")
    def test_handle_analysis_task_started(self, mock_status_tracker, mock_workflow_logger, view_model):
        """Test that analysis task started is handled correctly."""
        test_task_id = "test_task_123"

        with patch.object(view_model, "_run_worker") as mock_run_worker:
            view_model._handle_analysis_task_started(test_task_id)

            # Verify logging and status tracking
            mock_workflow_logger.log_api_response.assert_called_once()
            mock_status_tracker.set_task_id.assert_called_once_with(test_task_id)
            mock_status_tracker.update_status.assert_called_once()

            # Verify polling worker is started
            mock_run_worker.assert_called_once()

    @patch("src.gui.view_models.main_view_model.workflow_logger")
    @patch("src.gui.view_models.main_view_model.status_tracker")
    def test_on_analysis_polling_success(self, mock_status_tracker, mock_workflow_logger, view_model):
        """Test successful analysis polling completion."""
        test_result = {"analysis": {"findings": []}, "status": "complete"}

        # Mock the signal emission
        view_model.analysis_result_received = Mock()

        view_model._on_analysis_polling_success(test_result)

        # Verify logging and status tracking
        mock_workflow_logger.log_workflow_completion.assert_called_once_with(True, test_result)
        mock_status_tracker.complete_analysis.assert_called_once_with(test_result)

        # Verify signal emission
        view_model.analysis_result_received.emit.assert_called_once_with(test_result)

    @patch("src.gui.view_models.main_view_model.workflow_logger")
    @patch("src.gui.view_models.main_view_model.status_tracker")
    @patch("src.gui.view_models.main_view_model.error_handler")
    def test_handle_analysis_error_with_logging(
        self, mock_error_handler, mock_status_tracker, mock_workflow_logger, view_model
    ):
        """Test analysis error handling with logging."""
        test_error = "Analysis failed: timeout"
        mock_analysis_error = Mock()
        mock_analysis_error.icon = "❌"
        mock_analysis_error.severity = "critical"
        mock_error_handler.categorize_and_handle_error.return_value = mock_analysis_error
        mock_error_handler.format_error_message.return_value = "Formatted error message"

        # Mock the signal emission
        view_model.show_message_box_signal = Mock()

        view_model._handle_analysis_error_with_logging(test_error)

        # Verify error processing
        mock_error_handler.categorize_and_handle_error.assert_called_once_with(test_error)
        mock_error_handler.format_error_message.assert_called()

        # Verify logging and status tracking
        mock_workflow_logger.log_workflow_completion.assert_called_once_with(False, error=test_error)
        mock_status_tracker.set_error.assert_called_once_with(test_error)

        # Verify signal emission
        view_model.show_message_box_signal.emit.assert_called_once()

    def test_stop_all_workers(self, view_model):
        """Test that stop_all_workers properly terminates threads."""
        # Create mock threads
        mock_thread1 = Mock()
        mock_thread2 = Mock()
        mock_thread1.isRunning.return_value = True
        mock_thread2.isRunning.return_value = False

        view_model._active_threads = [mock_thread1, mock_thread2]

        view_model.stop_all_workers()

        # Verify running thread was quit
        mock_thread1.quit.assert_called_once()
        mock_thread1.wait.assert_called_once_with(2000)

        # Verify non-running thread was not quit
        mock_thread2.quit.assert_not_called()

        # Verify threads list was cleared
        assert len(view_model._active_threads) == 0

    def test_load_meta_analytics_with_params(self, view_model):
        """Test load_meta_analytics with custom parameters."""
        test_params = {"days_back": 30, "discipline": "pt"}

        with patch.object(view_model, "_run_worker") as mock_run_worker:
            view_model.load_meta_analytics(test_params)

            mock_run_worker.assert_called_once()
            call_args = mock_run_worker.call_args
            expected_endpoint = "/meta-analytics/widget_data?days_back=30&discipline=pt"
            assert call_args.kwargs["endpoint"] == expected_endpoint

    def test_load_meta_analytics_without_params(self, view_model):
        """Test load_meta_analytics without parameters."""
        with patch.object(view_model, "_run_worker") as mock_run_worker:
            view_model.load_meta_analytics()

            mock_run_worker.assert_called_once()
            call_args = mock_run_worker.call_args
            assert call_args.kwargs["endpoint"] == "/meta-analytics/widget_data"

    @patch("src.gui.view_models.main_view_model.requests")
    def test_save_settings(self, mock_requests, view_model):
        """Test settings save functionality."""
        test_settings = {"theme": "dark", "auto_save": True}
        mock_response = Mock()
        mock_response.json.return_value = {"message": "Settings saved"}
        mock_requests.post.return_value = mock_response

        with patch.object(view_model, "_run_worker") as mock_run_worker:
            view_model.save_settings(test_settings)

            # Verify _run_worker was called with SettingsSaveWorker
            mock_run_worker.assert_called_once()

    def test_submit_feedback(self, view_model):
        """Test feedback submission."""
        test_feedback = {"finding_id": "123", "is_correct": True}

        with patch.object(view_model, "_run_worker") as mock_run_worker:
            view_model.submit_feedback(test_feedback)

            mock_run_worker.assert_called_once()
            call_args = mock_run_worker.call_args
            assert call_args.kwargs["feedback_data"] == test_feedback
