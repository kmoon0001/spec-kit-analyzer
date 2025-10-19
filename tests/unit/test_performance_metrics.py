"""Comprehensive unit tests for performance metrics collection."""

import pytest
import time
from unittest.mock import Mock, patch
from src.core.performance_metrics_collector import (
    MetricsCollector,
    PerformanceMetrics,
    RequestTimer,
    DatabaseQueryTimer,
    AIInferenceTimer
)


class TestMetricsCollector:
    """Test suite for MetricsCollector."""

    @pytest.fixture
    def metrics_collector(self):
        """Create MetricsCollector instance."""
        return MetricsCollector(max_history=100)

    def test_request_recording(self, metrics_collector):
        """Test request metrics are recorded properly."""
        metrics_collector.record_request(150.5, 200, "/test")

        current = metrics_collector.get_current_metrics()
        assert current.request_count == 1
        assert current.request_duration_ms == 150.5
        assert current.error_count == 0

    def test_error_request_recording(self, metrics_collector):
        """Test error requests are recorded properly."""
        metrics_collector.record_request(200.0, 400, "/test")

        current = metrics_collector.get_current_metrics()
        assert current.request_count == 1
        assert current.error_count == 1

    def test_database_query_recording(self, metrics_collector):
        """Test database query metrics are recorded."""
        metrics_collector.record_database_query(50.0, "SELECT")

        current = metrics_collector.get_current_metrics()
        assert current.database_query_count == 1
        assert current.database_query_duration_ms == 50.0

    def test_ai_inference_recording(self, metrics_collector):
        """Test AI inference metrics are recorded."""
        metrics_collector.record_ai_inference(1000.0, "llama")

        current = metrics_collector.get_current_metrics()
        assert current.ai_inference_count == 1
        assert current.ai_inference_duration_ms == 1000.0

    def test_cache_operation_recording(self, metrics_collector):
        """Test cache operation metrics are recorded."""
        # Record some requests first
        metrics_collector.record_request(100.0, 200, "/test")
        metrics_collector.record_request(100.0, 200, "/test")

        # Record cache hits
        metrics_collector.record_cache_operation(True, "memory")
        metrics_collector.record_cache_operation(True, "memory")
        metrics_collector.record_cache_operation(False, "memory")

        current = metrics_collector.get_current_metrics()
        assert current.cache_hit_rate == 100.0  # All operations were hits (2 hits, 1 miss = 100% hit rate)

    def test_custom_metric_recording(self, metrics_collector):
        """Test custom metrics are recorded."""
        metrics_collector.record_custom_metric("custom_metric", 42.5, {"tag": "value"})

        assert "custom_metric" in metrics_collector.custom_metrics
        assert len(metrics_collector.custom_metrics["custom_metric"]) == 1
        assert metrics_collector.custom_metrics["custom_metric"][0].value == 42.5
        assert metrics_collector.custom_metrics["custom_metric"][0].tags == {"tag": "value"}

    def test_slow_request_warning(self, metrics_collector):
        """Test slow requests trigger warnings."""
        with patch('src.core.performance_metrics_collector.logger') as mock_logger:
            metrics_collector.record_request(6000.0, 200, "/slow-endpoint")

            mock_logger.warning.assert_called_once()
            assert "Slow request detected" in str(mock_logger.warning.call_args)
            assert "/slow-endpoint" in str(mock_logger.warning.call_args)

    def test_slow_database_query_warning(self, metrics_collector):
        """Test slow database queries trigger warnings."""
        with patch('src.core.performance_metrics_collector.logger') as mock_logger:
            metrics_collector.record_database_query(2000.0, "SELECT")

            mock_logger.warning.assert_called_once()
            assert "Slow database query detected" in str(mock_logger.warning.call_args)

    def test_slow_ai_inference_warning(self, metrics_collector):
        """Test slow AI inference triggers warnings."""
        with patch('src.core.performance_metrics_collector.logger') as mock_logger:
            metrics_collector.record_ai_inference(15000.0, "llama")

            mock_logger.warning.assert_called_once()
            assert "Slow AI inference detected" in str(mock_logger.warning.call_args)

    def test_system_metrics_update(self, metrics_collector):
        """Test system metrics are updated."""
        with patch('src.core.performance_metrics_collector.psutil') as mock_psutil:
            # Mock process and system info
            mock_process = Mock()
            mock_process.memory_info.return_value = Mock(rss=100 * 1024 * 1024)  # 100MB
            mock_psutil.Process.return_value = mock_process
            mock_psutil.cpu_percent.return_value = 25.5

            metrics_collector.update_system_metrics()

            current = metrics_collector.get_current_metrics()
            assert current.memory_usage_mb == 100.0
            assert current.cpu_usage_percent == 25.5

    def test_high_memory_warning(self, metrics_collector):
        """Test high memory usage triggers warnings."""
        with patch('src.core.performance_metrics_collector.psutil') as mock_psutil:
            mock_process = Mock()
            mock_process.memory_info.return_value = Mock(rss=2000 * 1024 * 1024)  # 2GB
            mock_psutil.Process.return_value = mock_process
            mock_psutil.cpu_percent.return_value = 50.0

            with patch('src.core.performance_metrics_collector.logger') as mock_logger:
                metrics_collector.update_system_metrics()

                mock_logger.warning.assert_called_once()
                assert "High memory usage detected" in str(mock_logger.warning.call_args)

    def test_high_cpu_warning(self, metrics_collector):
        """Test high CPU usage triggers warnings."""
        with patch('src.core.performance_metrics_collector.psutil') as mock_psutil:
            mock_process = Mock()
            mock_process.memory_info.return_value = Mock(rss=100 * 1024 * 1024)  # 100MB
            mock_psutil.Process.return_value = mock_process
            mock_psutil.cpu_percent.return_value = 90.0

            with patch('src.core.performance_metrics_collector.logger') as mock_logger:
                metrics_collector.update_system_metrics()

                mock_logger.warning.assert_called_once()
                assert "High CPU usage detected" in str(mock_logger.warning.call_args)

    def test_metrics_summary_calculation(self, metrics_collector):
        """Test metrics summary is calculated correctly."""
        # Record some metrics
        metrics_collector.record_request(100.0, 200, "/test")
        metrics_collector.record_request(200.0, 200, "/test")
        metrics_collector.record_request(300.0, 400, "/test")  # Error

        metrics_collector.record_database_query(50.0, "SELECT")
        metrics_collector.record_database_query(75.0, "INSERT")

        metrics_collector.record_ai_inference(1000.0, "llama")

        summary = metrics_collector.get_metrics_summary()

        assert summary["requests"]["total"] == 3
        assert summary["requests"]["avg_duration_ms"] == 200.0
        assert summary["requests"]["error_count"] == 1
        assert summary["requests"]["error_rate_percent"] == 33.33

        assert summary["database"]["query_count"] == 2
        assert summary["database"]["avg_duration_ms"] == 62.5

        assert summary["ai_inference"]["count"] == 1
        assert summary["ai_inference"]["avg_duration_ms"] == 1000.0

    def test_metrics_reset(self, metrics_collector):
        """Test metrics can be reset."""
        # Record some metrics
        metrics_collector.record_request(100.0, 200, "/test")
        metrics_collector.record_custom_metric("test", 42.0)

        # Reset
        metrics_collector.reset_metrics()

        current = metrics_collector.get_current_metrics()
        assert current.request_count == 0
        assert len(metrics_collector.custom_metrics) == 0
        assert len(metrics_collector.metrics_history) == 0

    def test_history_limit(self, metrics_collector):
        """Test metrics history is limited."""
        # Record more metrics than the limit
        for i in range(150):
            metrics_collector.record_custom_metric("test", float(i))

        assert len(metrics_collector.custom_metrics["test"]) == 100  # max_history
        assert metrics_collector.custom_metrics["test"][0].value == 50.0  # First kept item


class TestContextManagers:
    """Test suite for context managers."""

    def test_request_timer(self):
        """Test RequestTimer context manager."""
        with patch('src.core.performance_metrics_collector.metrics_collector') as mock_collector:
            with RequestTimer("/test", 200) as timer:
                time.sleep(0.001)  # Small delay

            mock_collector.record_request.assert_called_once()
            call_args = mock_collector.record_request.call_args
            assert call_args[0][1] == 200  # status_code
            assert call_args[0][2] == "/test"  # endpoint

    def test_database_query_timer(self):
        """Test DatabaseQueryTimer context manager."""
        with patch('src.core.performance_metrics_collector.metrics_collector') as mock_collector:
            with DatabaseQueryTimer("SELECT") as timer:
                time.sleep(0.001)  # Small delay

            mock_collector.record_database_query.assert_called_once()
            call_args = mock_collector.record_database_query.call_args
            assert call_args[0][1] == "SELECT"  # query_type

    def test_ai_inference_timer(self):
        """Test AIInferenceTimer context manager."""
        with patch('src.core.performance_metrics_collector.metrics_collector') as mock_collector:
            with AIInferenceTimer("llama") as timer:
                time.sleep(0.001)  # Small delay

            mock_collector.record_ai_inference.assert_called_once()
            call_args = mock_collector.record_ai_inference.call_args
            assert call_args[0][1] == "llama"  # model_type

    def test_context_manager_exception_handling(self):
        """Test context managers handle exceptions properly."""
        with patch('src.core.performance_metrics_collector.metrics_collector') as mock_collector:
            try:
                with RequestTimer("/test", 200):
                    raise Exception("Test error")
            except Exception:
                pass

            # Should still record the request
            mock_collector.record_request.assert_called_once()
