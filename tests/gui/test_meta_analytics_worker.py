"""
Tests for MetaAnalyticsWorker.

Tests the background worker for loading organizational analytics data.
"""

from unittest.mock import Mock, patch

from src.gui.workers.meta_analytics_worker import MetaAnalyticsWorker


class TestMetaAnalyticsWorker:
    """Test cases for MetaAnalyticsWorker."""

    def test_worker_initialization(self):
        """Test worker initializes with correct parameters."""
        token = "test_token"
        worker = MetaAnalyticsWorker(token)

        assert worker.token == token
        assert worker.days_back == 90
        assert worker.discipline is None
        assert worker.load_type == "overview"

    def test_set_parameters(self):
        """Test parameter setting functionality."""
        worker = MetaAnalyticsWorker("test_token")

        worker.set_parameters(days_back=30, discipline="PT", load_type="training")

        assert worker.days_back == 30
        assert worker.discipline == "PT"
        assert worker.load_type == "training"

    def test_set_peer_comparison(self):
        """Test peer comparison setup."""
        worker = MetaAnalyticsWorker("test_token")

        worker.set_peer_comparison(user_id=123, days_back=60)

        assert worker.days_back == 60
        assert worker.load_type == "peer_comparison_123"

    @patch("src.gui.workers.meta_analytics_worker.requests.get")
    def test_successful_overview_loading(self, mock_get):
        """Test successful organizational overview loading."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "organizational_metrics": {"total_users": 10},
            "training_needs": [],
            "insights": [],
        }
        mock_get.return_value = mock_response

        worker = MetaAnalyticsWorker("test_token")

        # Mock signals
        success_data = None
        error_msg = None

        def capture_success(data):
            nonlocal success_data
            success_data = data

        def capture_error(msg):
            nonlocal error_msg
            error_msg = msg

        worker.success.connect(capture_success)
        worker.error.connect(capture_error)

        # Run the worker
        worker.run()

        # Verify success
        assert success_data is not None
        assert error_msg is None
        assert success_data["organizational_metrics"]["total_users"] == 10

    @patch("src.gui.workers.meta_analytics_worker.requests.get")
    def test_api_error_handling(self, mock_get):
        """Test API error handling."""
        # Mock API error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_get.return_value = mock_response

        worker = MetaAnalyticsWorker("test_token")

        # Mock signals
        success_data = None
        error_msg = None

        def capture_success(data):
            nonlocal success_data
            success_data = data

        def capture_error(msg):
            nonlocal error_msg
            error_msg = msg

        worker.success.connect(capture_success)
        worker.error.connect(capture_error)

        # Run the worker
        worker.run()

        # Verify error handling
        assert success_data is None
        assert error_msg is not None
        assert ("Failed to load analytics" in error_msg or "An unexpected error occurred" in error_msg)
