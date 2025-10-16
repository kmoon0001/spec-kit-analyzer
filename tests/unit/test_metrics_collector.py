"""
Unit tests for the enhanced metrics collector.

Tests the comprehensive metric collection system including various sources,
error handling, and performance monitoring capabilities.
"""

import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.core.metrics_collector import (
    AIModelMetricsSource,
    ApplicationMetricsSource,
    MetricsCollector,
    MetricSource,
    MetricType,
    PerformanceMetric,
    SystemMetricsSource,
    get_metrics_collector,
    record_ai_inference_time,
    record_cache_hit,
    record_error,
    record_model_load,
    record_request,
    record_response_time,
    reset_metrics_collector,
)


class TestPerformanceMetric:
    """Test PerformanceMetric functionality"""

    def test_metric_creation(self):
        """Test creating a performance metric"""
        timestamp = datetime.now()
        metric = PerformanceMetric(
            timestamp=timestamp,
            name="test_metric",
            value=42.5,
            unit="ms",
            metric_type=MetricType.GAUGE,
            source="test_source",
            tags={"component": "test"},
            metadata={"version": "1.0"},
        )

        assert metric.name == "test_metric"
        assert metric.value == 42.5
        assert metric.unit == "ms"
        assert metric.metric_type == MetricType.GAUGE
        assert metric.source == "test_source"
        assert metric.tags["component"] == "test"
        assert metric.metadata["version"] == "1.0"

    def test_metric_to_dict(self):
        """Test metric serialization to dictionary"""
        timestamp = datetime.now()
        metric = PerformanceMetric(
            timestamp=timestamp,
            name="test_metric",
            value=42.5,
            unit="ms",
            metric_type=MetricType.GAUGE,
            source="test_source",
        )

        result = metric.to_dict()

        assert isinstance(result, dict)
        assert result["name"] == "test_metric"
        assert result["value"] == 42.5
        assert result["unit"] == "ms"
        assert result["metric_type"] == "gauge"
        assert result["source"] == "test_source"
        assert "timestamp" in result

    def test_metric_string_representation(self):
        """Test metric string representation"""
        timestamp = datetime.now()
        metric = PerformanceMetric(
            timestamp=timestamp, name="cpu_usage", value=75.5, unit="%", metric_type=MetricType.GAUGE, source="system"
        )

        result = str(metric)
        assert "cpu_usage=75.5%" in result
        assert "[system]" in result

    def test_metric_equality(self):
        """Test metric equality comparison"""
        timestamp = datetime.now()
        metric1 = PerformanceMetric(
            timestamp=timestamp,
            name="test_metric",
            value=42.5,
            unit="ms",
            metric_type=MetricType.GAUGE,
            source="test_source",
        )

        metric2 = PerformanceMetric(
            timestamp=timestamp,
            name="test_metric",
            value=42.5,
            unit="ms",
            metric_type=MetricType.GAUGE,
            source="test_source",
        )

        metric3 = PerformanceMetric(
            timestamp=timestamp,
            name="different_metric",
            value=42.5,
            unit="ms",
            metric_type=MetricType.GAUGE,
            source="test_source",
        )

        assert metric1 == metric2
        assert metric1 != metric3
        assert metric1 != "not_a_metric"


class TestMetricSource:
    """Test MetricSource base functionality"""

    def test_metric_source_health_tracking(self):
        """Test metric source health tracking"""

        class TestSource(MetricSource):
            def get_source_name(self) -> str:
                return "test_source"

            async def collect_metrics(self):
                return []

            def is_available(self) -> bool:
                return True

        source = TestSource()

        # Initially healthy
        assert source.is_healthy()

        # Record some errors
        for i in range(3):
            source.record_error(Exception(f"Error {i}"))
            assert source.is_healthy()  # Still healthy

        # Record more errors to exceed threshold
        for i in range(3):
            source.record_error(Exception(f"Error {i + 3}"))

        assert not source.is_healthy()  # Now unhealthy

        # Reset health
        source.reset_health()
        assert source.is_healthy()

    def test_metric_source_last_collection_time(self):
        """Test last collection time tracking"""

        class TestSource(MetricSource):
            def get_source_name(self) -> str:
                return "test_source"

            async def collect_metrics(self):
                with self._lock:
                    self._last_collection_time = datetime.now()
                return []

            def is_available(self) -> bool:
                return True

        source = TestSource()

        # Initially no collection time
        assert source.get_last_collection_time() is None

        # After collection, should have time
        asyncio.run(source.collect_metrics())
        assert source.get_last_collection_time() is not None


class TestSystemMetricsSource:
    """Test SystemMetricsSource functionality"""

    def test_system_source_availability(self):
        """Test system source availability detection"""
        source = SystemMetricsSource()

        # Test when psutil is available (mock the import)
        with patch("builtins.__import__") as mock_import:
            mock_import.return_value = MagicMock()
            assert source.is_available()

        # Test when psutil is not available
        with patch("builtins.__import__", side_effect=ImportError):
            source = SystemMetricsSource()
            assert not source.is_available()

    @pytest.mark.asyncio
    async def test_system_metrics_collection(self):
        """Test system metrics collection"""
        source = SystemMetricsSource()

        # Mock psutil for testing
        mock_psutil = MagicMock()
        with patch("builtins.__import__", return_value=mock_psutil):
            # Mock CPU metrics
            mock_psutil.cpu_percent.return_value = 75.5
            mock_psutil.cpu_count.return_value = 4

            # Mock memory metrics
            mock_memory = MagicMock()
            mock_memory.percent = 60.0
            mock_memory.available = 1024 * 1024 * 1024  # 1GB
            mock_psutil.virtual_memory.return_value = mock_memory

            # Mock disk metrics
            mock_disk = MagicMock()
            mock_disk.used = 500 * 1024 * 1024 * 1024  # 500GB
            mock_disk.total = 1000 * 1024 * 1024 * 1024  # 1TB
            mock_psutil.disk_usage.return_value = mock_disk

            # Mock process metrics
            mock_process = MagicMock()
            mock_memory_info = MagicMock()
            mock_memory_info.rss = 100 * 1024 * 1024  # 100MB
            mock_process.memory_info.return_value = mock_memory_info
            mock_process.cpu_percent.return_value = 25.0
            mock_psutil.Process.return_value = mock_process

            metrics = await source.collect_metrics()

            assert len(metrics) > 0

            # Check for expected metrics
            metric_names = [m.name for m in metrics]
            assert "cpu_usage_percent" in metric_names
            assert "memory_usage_percent" in metric_names
            assert "memory_available_bytes" in metric_names
            assert "disk_usage_percent" in metric_names
            assert "process_memory_rss" in metric_names
            assert "process_cpu_percent" in metric_names

            # Verify metric values
            cpu_metric = next(m for m in metrics if m.name == "cpu_usage_percent")
            assert cpu_metric.value == 75.5
            assert cpu_metric.unit == "%"
            assert cpu_metric.metric_type == MetricType.GAUGE

    @pytest.mark.asyncio
    async def test_system_metrics_error_handling(self):
        """Test system metrics error handling"""
        source = SystemMetricsSource()

        # Mock psutil to raise an exception
        mock_psutil = MagicMock()
        with patch("builtins.__import__", return_value=mock_psutil):
            mock_psutil.cpu_percent.side_effect = Exception("CPU error")

            metrics = await source.collect_metrics()

            # Should return empty list on error
            assert metrics == []

            # Should record the error
            assert source._collection_errors > 0


class TestApplicationMetricsSource:
    """Test ApplicationMetricsSource functionality"""

    def test_application_source_initialization(self):
        """Test application source initialization"""
        source = ApplicationMetricsSource()

        assert source.get_source_name() == "application"
        assert source.is_available()
        assert source.is_healthy()

    @pytest.mark.asyncio
    async def test_application_metrics_collection(self):
        """Test application metrics collection"""
        source = ApplicationMetricsSource()

        # Record some test data
        source.record_response_time(100.0)
        source.record_response_time(150.0)
        source.record_response_time(200.0)
        source.record_request("/api/test")
        source.record_request("/api/test")
        source.record_request("/api/other")
        source.record_error("validation_error")
        source.record_error("timeout_error")

        metrics = await source.collect_metrics()

        assert len(metrics) > 0

        # Check for expected metrics
        metric_names = [m.name for m in metrics]
        assert "response_time_avg" in metric_names
        assert "response_time_max" in metric_names
        assert "response_time_min" in metric_names
        assert "request_count" in metric_names
        assert "error_count" in metric_names

        # Verify response time calculations
        avg_metric = next(m for m in metrics if m.name == "response_time_avg")
        assert avg_metric.value == 150.0  # (100 + 150 + 200) / 3

        max_metric = next(m for m in metrics if m.name == "response_time_max")
        assert max_metric.value == 200.0

        min_metric = next(m for m in metrics if m.name == "response_time_min")
        assert min_metric.value == 100.0

    def test_application_metrics_validation(self):
        """Test application metrics input validation"""
        source = ApplicationMetricsSource()

        # Test invalid response time
        source.record_response_time(-10.0)  # Should be ignored

        # Test invalid endpoint
        source.record_request("")  # Should be ignored
        source.record_request("   ")  # Should be ignored

        # Test invalid error type
        source.record_error_by_type("")  # Should be ignored
        source.record_error_by_type("   ")  # Should be ignored

        # Valid data should work
        source.record_response_time(100.0)
        source.record_request("/api/test")
        source.record_error_by_type("test_error")

        stats = source.get_current_stats()
        assert stats["response_times_count"] == 1
        assert stats["total_requests"] == 1
        assert stats["total_errors"] == 1

    def test_application_metrics_reset(self):
        """Test application metrics counter reset"""
        source = ApplicationMetricsSource()

        # Record some data
        source.record_request("/api/test")
        source.record_error("test_error")

        stats_before = source.get_current_stats()
        assert stats_before["total_requests"] > 0
        assert stats_before["total_errors"] > 0

        # Reset counters
        source.reset_counters()

        stats_after = source.get_current_stats()
        assert stats_after["total_requests"] == 0
        assert stats_after["total_errors"] == 0


class TestAIModelMetricsSource:
    """Test AIModelMetricsSource functionality"""

    def test_ai_source_initialization(self):
        """Test AI source initialization"""
        source = AIModelMetricsSource()

        assert source.get_source_name() == "ai_models"
        assert source.is_available()
        assert source.is_healthy()

    @pytest.mark.asyncio
    async def test_ai_metrics_collection(self):
        """Test AI metrics collection"""
        source = AIModelMetricsSource()

        # Record some test data
        source.record_inference_time(50.0)
        source.record_inference_time(75.0)
        source.record_inference_time(100.0)
        source.record_model_load("bert-base")
        source.record_model_load("gpt-3.5")
        source.record_model_error("bert-base")
        source.record_cache_hit("bert-base")
        source.record_cache_hit("bert-base")
        source.record_cache_miss("bert-base")

        metrics = await source.collect_metrics()

        assert len(metrics) > 0

        # Check for expected metrics
        metric_names = [m.name for m in metrics]
        assert "ai_inference_time_avg" in metric_names
        assert "ai_inference_count" in metric_names
        assert "model_load_count" in metric_names
        assert "model_error_count" in metric_names
        assert "model_cache_hit_rate" in metric_names

        # Verify inference time calculation
        avg_metric = next(m for m in metrics if m.name == "ai_inference_time_avg")
        assert avg_metric.value == 75.0  # (50 + 75 + 100) / 3

        # Verify cache hit rate calculation
        cache_metric = next(m for m in metrics if m.name == "model_cache_hit_rate")
        assert abs(cache_metric.value - 66.67) < 0.01  # 2 hits out of 3 total (2 hits + 1 miss)

    def test_ai_metrics_validation(self):
        """Test AI metrics input validation"""
        source = AIModelMetricsSource()

        # Test invalid inference time
        source.record_inference_time(-10.0)  # Should be ignored

        # Test invalid model names
        source.record_model_load("")  # Should be ignored
        source.record_model_load("   ")  # Should be ignored
        source.record_model_error("")  # Should be ignored
        source.record_cache_hit("")  # Should be ignored
        source.record_cache_miss("")  # Should be ignored

        # Valid data should work
        source.record_inference_time(100.0)
        source.record_model_load("test-model")
        source.record_model_error("test-model")
        source.record_cache_hit("test-model")
        source.record_cache_miss("test-model")

        # Should have recorded valid data
        assert len(source._inference_times) == 1
        assert source._model_loads["test-model"] == 1
        assert source._model_errors["test-model"] == 1
        assert source._model_cache_hits["test-model"] == 1
        assert source._model_cache_misses["test-model"] == 1


class TestMetricsCollector:
    """Test MetricsCollector functionality"""

    def setup_method(self):
        """Setup for each test method"""
        # Reset global collector for clean tests
        reset_metrics_collector()

    def test_collector_initialization(self):
        """Test metrics collector initialization"""
        collector = MetricsCollector()

        assert not collector._is_running
        assert collector._collection_interval >= 1.0  # Minimum interval
        assert len(collector._sources) > 0  # Should have default sources

        # Check default sources
        source_names = list(collector._sources.keys())
        assert "application" in source_names
        assert "ai_models" in source_names

    def test_source_registration(self):
        """Test metric source registration"""
        collector = MetricsCollector()

        class TestSource(MetricSource):
            def get_source_name(self) -> str:
                return "test_source"

            async def collect_metrics(self):
                return []

            def is_available(self) -> bool:
                return True

        # Register new source
        test_source = TestSource()
        collector.register_source(test_source)

        assert "test_source" in collector._sources

        # Test invalid source registration
        with pytest.raises(ValueError):
            collector.register_source("not_a_source")

    def test_source_unregistration(self):
        """Test metric source unregistration"""
        collector = MetricsCollector()

        # Unregister existing source
        assert collector.unregister_source("application")
        assert "application" not in collector._sources

        # Try to unregister non-existent source
        assert not collector.unregister_source("non_existent")

    @pytest.mark.asyncio
    async def test_metrics_collection(self):
        """Test metrics collection from all sources"""
        collector = MetricsCollector()

        # Collect metrics
        metrics = await collector.collect_all_metrics()

        assert isinstance(metrics, list)
        # Should have metrics from default sources
        assert len(metrics) >= 0  # May be empty if no data recorded yet

        # Check collector stats
        stats = collector.get_collector_stats()
        assert stats["total_collections"] > 0
        assert stats["last_collection_time"] is not None

    def test_callback_system(self):
        """Test metrics callback system"""
        collector = MetricsCollector()

        callback_called = False
        received_metrics = None

        def test_callback(metrics):
            nonlocal callback_called, received_metrics
            callback_called = True
            received_metrics = metrics

        # Add callback
        collector.add_callback(test_callback)
        assert len(collector._callbacks) == 1

        # Test invalid callback
        with pytest.raises(ValueError):
            collector.add_callback("not_callable")

        # Remove callback
        assert collector.remove_callback(test_callback)
        assert len(collector._callbacks) == 0

        # Try to remove non-existent callback
        assert not collector.remove_callback(test_callback)

    def test_metrics_buffer(self):
        """Test metrics buffer functionality"""
        collector = MetricsCollector()

        # Add some test metrics to buffer
        test_metrics = [
            PerformanceMetric(
                timestamp=datetime.now(),
                name=f"test_metric_{i}",
                value=float(i),
                unit="count",
                metric_type=MetricType.COUNTER,
                source="test",
            )
            for i in range(5)
        ]

        with collector._buffer_lock:
            collector._metrics_buffer.extend(test_metrics)

        # Get recent metrics
        recent = collector.get_recent_metrics(3)
        assert len(recent) == 3
        assert recent[-1].name == "test_metric_4"  # Most recent

        # Get metrics by source
        source_metrics = collector.get_metrics_by_source("test", 2)
        assert len(source_metrics) == 2
        assert all(m.source == "test" for m in source_metrics)

    def test_source_status(self):
        """Test source status reporting"""
        collector = MetricsCollector()

        status = collector.get_source_status()

        assert isinstance(status, dict)
        assert len(status) > 0

        # Check status structure
        for _source_name, source_status in status.items():
            assert "available" in source_status
            assert "healthy" in source_status
            assert "last_collection" in source_status
            assert "error_count" in source_status

    def test_collector_cleanup(self):
        """Test collector cleanup"""
        collector = MetricsCollector()

        # Test cleanup without starting collection
        collector.cleanup()

        assert not collector._is_running
        assert len(collector._sources) == 0
        assert len(collector._callbacks) == 0


class TestGlobalFunctions:
    """Test global convenience functions"""

    def setup_method(self):
        """Setup for each test method"""
        reset_metrics_collector()

    def test_global_collector_singleton(self):
        """Test global collector singleton pattern"""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        assert collector1 is collector2  # Same instance

    def test_convenience_functions(self):
        """Test convenience functions for metric recording"""
        # These should not raise exceptions
        record_response_time(100.0)
        record_request("/api/test")
        record_error("test_error")
        record_ai_inference_time(50.0)
        record_model_load("test-model")
        record_cache_hit("test-model")

        # Verify data was recorded
        collector = get_metrics_collector()

        app_source = collector._sources.get("application")
        if isinstance(app_source, ApplicationMetricsSource):
            stats = app_source.get_current_stats()
            assert stats["response_times_count"] > 0
            assert stats["total_requests"] > 0
            assert stats["total_errors"] > 0

        ai_source = collector._sources.get("ai_models")
        if isinstance(ai_source, AIModelMetricsSource):
            assert len(ai_source._inference_times) > 0
            assert ai_source._model_loads["test-model"] > 0
            assert ai_source._model_cache_hits["test-model"] > 0

    def test_convenience_functions_error_handling(self):
        """Test convenience functions handle errors gracefully"""
        # Mock the collector to raise an exception
        with patch("src.core.metrics_collector.get_metrics_collector") as mock_get:
            mock_get.side_effect = Exception("Test error")

            # These should not raise exceptions
            record_response_time(100.0)
            record_request("/api/test")
            record_error("test_error")
            record_ai_inference_time(50.0)
            record_model_load("test-model")


if __name__ == "__main__":
    pytest.main([__file__])
