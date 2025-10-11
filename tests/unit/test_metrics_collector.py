"""
Unit tests for the enhanced metrics collector.

Tests the comprehensive metric collection system including various sources,
error handling, and performance monitoring capabilities.
"""

import asyncio
import pytest
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.metrics_collector import (
    MetricType,
    PerformanceMetric,
    MetricSource,
    SystemMetricsSource,
    ApplicationMetricsSource,
    AIModelMetricsSource,
    MetricsCollector,
    get_metrics_collector,
    record_response_time,
    record_request,
    record_error,
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
            metadata={"version": "1.0"}
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
            source="test_source"
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
            timestamp=timestamp,
            name="cpu_usage",
            value=75.5,
            unit="%",
            metric_type=MetricType.GAUGE,
            source="system"
        )
        
        result = str(metric)
        assert "cpu_usage=75.5%" in result
        assert "[system]" in result


class TestMetricSource:
    """Test MetricSource base functionality"""

    def test_metric_source_health_tracking(self):
        """Test metric source health tracking"""
        
        class TestSource(MetricSource):
            def get_source_name(self) -> str:
                return "test"
            
            async def collect_metrics(self):
                return []
            
            def is_available(self) -> bool:
                return True
        
        source = TestSource()
        
        # Initially healthy
        assert source.is_healthy()
        assert source._collection_errors == 0
        
        # Record some errors
        for i in range(3):
            source.record_error(Exception(f"Error {i}"))
        
        # Still healthy (under threshold)
        assert source.is_healthy()
        assert source._collection_errors == 3
        
        # Record more errors to exceed threshold
        for i in range(3):
            source.record_error(Exception(f"Error {i+3}"))
        
        # Now unhealthy
        assert not source.is_healthy()
        assert source._collection_errors >= 5
        
        # Reset health
        source.reset_health()
        assert source.is_healthy()
        assert source._collection_errors == 0


class TestSystemMetricsSource:
    """Test SystemMetricsSource functionality"""

    def test_source_name(self):
        """Test system metrics source name"""
        source = SystemMetricsSource()
        assert source.get_source_name() == "system"

    def test_is_available_with_psutil(self):
        """Test availability check when psutil is available"""
        with patch('builtins.__import__', return_value=MagicMock()):
            source = SystemMetricsSource()
            assert source.is_available() is True

    def test_is_available_without_psutil(self):
        """Test availability check when psutil is not available"""
        def mock_import(name, *args, **kwargs):
            if name == 'psutil':
                raise ImportError("No module named 'psutil'")
            return __import__(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            source = SystemMetricsSource()
            assert source.is_available() is False

    @pytest.mark.asyncio
    async def test_collect_metrics_success(self):
        """Test successful metrics collection"""
        # Mock psutil module
        mock_psutil = MagicMock()
        mock_psutil.cpu_percent.return_value = 45.5
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=60.0, available=1000000, used=2000000
        )
        mock_psutil.disk_usage.return_value = MagicMock(
            total=10000000, used=5000000, free=5000000
        )
        mock_psutil.net_io_counters.return_value = MagicMock(
            bytes_sent=1000, bytes_recv=2000
        )
        mock_psutil.Process.return_value = MagicMock(
            memory_info=MagicMock(rss=500000),
            cpu_percent=MagicMock(return_value=25.0)
        )
        mock_psutil.cpu_count.return_value = 4
        
        def mock_import(name, *args, **kwargs):
            if name == 'psutil':
                return mock_psutil
            return __import__(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            source = SystemMetricsSource()
            metrics = await source.collect_metrics()
        
        assert len(metrics) > 0
        
        # Check that we have CPU metrics
        cpu_metrics = [m for m in metrics if "cpu" in m.name]
        assert len(cpu_metrics) > 0
        
        # Check that we have memory metrics
        memory_metrics = [m for m in metrics if "memory" in m.name]
        assert len(memory_metrics) > 0
        
        # Verify metric structure
        for metric in metrics:
            assert isinstance(metric, PerformanceMetric)
            assert metric.source == "system"
            assert isinstance(metric.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_collect_metrics_unavailable(self):
        """Test metrics collection when psutil is unavailable"""
        with patch.object(SystemMetricsSource, 'is_available', return_value=False):
            source = SystemMetricsSource()
            metrics = await source.collect_metrics()
            assert metrics == []


class TestApplicationMetricsSource:
    """Test ApplicationMetricsSource functionality"""

    def test_source_name(self):
        """Test application metrics source name"""
        source = ApplicationMetricsSource()
        assert source.get_source_name() == "application"

    def test_is_available(self):
        """Test application metrics source availability"""
        source = ApplicationMetricsSource()
        assert source.is_available() is True

    def test_record_response_time(self):
        """Test recording response times"""
        source = ApplicationMetricsSource()
        
        # Record some response times
        source.record_response_time(100.0)
        source.record_response_time(150.0)
        source.record_response_time(200.0)
        
        assert len(source._response_times) == 3
        assert 100.0 in source._response_times
        assert 150.0 in source._response_times
        assert 200.0 in source._response_times

    def test_record_request(self):
        """Test recording requests"""
        source = ApplicationMetricsSource()
        
        source.record_request("/api/analyze")
        source.record_request("/api/analyze")
        source.record_request("/api/dashboard")
        
        assert source._request_counts["/api/analyze"] == 2
        assert source._request_counts["/api/dashboard"] == 1

    def test_record_error(self):
        """Test recording errors"""
        source = ApplicationMetricsSource()
        
        source.record_error("ValidationError")
        source.record_error("ValidationError")
        source.record_error("DatabaseError")
        
        assert source._error_counts["ValidationError"] == 2
        assert source._error_counts["DatabaseError"] == 1

    @pytest.mark.asyncio
    async def test_collect_metrics(self):
        """Test collecting application metrics"""
        source = ApplicationMetricsSource()
        
        # Record some data
        source.record_response_time(100.0)
        source.record_response_time(200.0)
        source.record_request("/api/test")
        source.record_error("TestError")
        
        metrics = await source.collect_metrics()
        
        # Should have response time, request count, and error count metrics
        assert len(metrics) >= 3
        
        # Check metric types
        response_time_metrics = [m for m in metrics if "response_time" in m.name]
        request_metrics = [m for m in metrics if "request_count" in m.name]
        error_metrics = [m for m in metrics if "error_count" in m.name]
        
        assert len(response_time_metrics) > 0
        assert len(request_metrics) > 0
        assert len(error_metrics) > 0

    def test_reset_counters(self):
        """Test resetting counters"""
        source = ApplicationMetricsSource()
        
        source.record_request("/api/test")
        source.record_error("TestError")
        
        assert len(source._request_counts) > 0
        assert len(source._error_counts) > 0
        
        source.reset_counters()
        
        assert len(source._request_counts) == 0
        assert len(source._error_counts) == 0


class TestAIModelMetricsSource:
    """Test AIModelMetricsSource functionality"""

    def test_source_name(self):
        """Test AI model metrics source name"""
        source = AIModelMetricsSource()
        assert source.get_source_name() == "ai_models"

    def test_record_inference_time(self):
        """Test recording inference times"""
        source = AIModelMetricsSource()
        
        source.record_inference_time(500.0)
        source.record_inference_time(750.0)
        
        assert len(source._inference_times) == 2
        assert 500.0 in source._inference_times
        assert 750.0 in source._inference_times

    def test_record_model_load(self):
        """Test recording model loads"""
        source = AIModelMetricsSource()
        
        source.record_model_load("bert-base")
        source.record_model_load("bert-base")
        source.record_model_load("gpt-3.5")
        
        assert source._model_loads["bert-base"] == 2
        assert source._model_loads["gpt-3.5"] == 1

    @pytest.mark.asyncio
    async def test_collect_metrics(self):
        """Test collecting AI model metrics"""
        source = AIModelMetricsSource()
        
        # Record some data
        source.record_inference_time(500.0)
        source.record_model_load("test-model")
        source.record_model_error("test-model")
        
        metrics = await source.collect_metrics()
        
        # Should have inference time, model load, and error metrics
        assert len(metrics) >= 3
        
        # Verify metric structure
        for metric in metrics:
            assert isinstance(metric, PerformanceMetric)
            assert metric.source == "ai_models"


class TestMetricsCollector:
    """Test MetricsCollector functionality"""

    def test_collector_initialization(self):
        """Test metrics collector initialization"""
        collector = MetricsCollector()
        
        # Should have default sources registered
        assert len(collector._sources) > 0
        assert "application" in collector._sources
        assert "ai_models" in collector._sources

    def test_register_source(self):
        """Test registering a metric source"""
        collector = MetricsCollector()
        
        class TestSource(MetricSource):
            def get_source_name(self) -> str:
                return "test_source"
            
            async def collect_metrics(self):
                return []
            
            def is_available(self) -> bool:
                return True
        
        test_source = TestSource()
        collector.register_source(test_source)
        
        assert "test_source" in collector._sources
        assert collector._sources["test_source"] is test_source

    def test_unregister_source(self):
        """Test unregistering a metric source"""
        collector = MetricsCollector()
        
        # Should have application source by default
        assert "application" in collector._sources
        
        result = collector.unregister_source("application")
        assert result is True
        assert "application" not in collector._sources
        
        # Try to unregister non-existent source
        result = collector.unregister_source("non_existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_collect_all_metrics(self):
        """Test collecting metrics from all sources"""
        collector = MetricsCollector()
        
        metrics = await collector.collect_all_metrics()
        
        # Should have metrics from multiple sources
        assert len(metrics) > 0
        
        # Check that metrics are stored in buffer
        recent_metrics = collector.get_recent_metrics()
        assert len(recent_metrics) > 0

    def test_get_metrics_by_source(self):
        """Test getting metrics by source"""
        collector = MetricsCollector()
        
        # Add some test metrics to buffer
        test_metric = PerformanceMetric(
            timestamp=datetime.now(),
            name="test_metric",
            value=42.0,
            unit="test",
            metric_type=MetricType.GAUGE,
            source="test_source"
        )
        
        with collector._buffer_lock:
            collector._metrics_buffer.append(test_metric)
        
        # Get metrics by source
        test_metrics = collector.get_metrics_by_source("test_source")
        assert len(test_metrics) == 1
        assert test_metrics[0].name == "test_metric"

    def test_get_metrics_summary(self):
        """Test getting metrics summary"""
        collector = MetricsCollector()
        
        # Add some test metrics
        test_metrics = [
            PerformanceMetric(
                timestamp=datetime.now(),
                name=f"metric_{i}",
                value=float(i),
                unit="test",
                metric_type=MetricType.GAUGE,
                source="test_source"
            )
            for i in range(5)
        ]
        
        with collector._buffer_lock:
            collector._metrics_buffer.extend(test_metrics)
        
        summary = collector.get_metrics_summary()
        
        assert summary["total_metrics"] >= 5
        assert "test_source" in summary["sources"]
        assert "time_range" in summary
        assert "healthy_sources" in summary

    def test_callback_functionality(self):
        """Test callback functionality"""
        collector = MetricsCollector()
        
        callback_called = False
        received_metrics = []
        
        def test_callback(metrics):
            nonlocal callback_called, received_metrics
            callback_called = True
            received_metrics.extend(metrics)
        
        collector.add_callback(test_callback)
        
        # Manually trigger callback
        test_metrics = [PerformanceMetric(
            timestamp=datetime.now(),
            name="test",
            value=1.0,
            unit="test",
            metric_type=MetricType.GAUGE,
            source="test"
        )]
        
        for callback in collector._callbacks:
            callback(test_metrics)
        
        assert callback_called
        assert len(received_metrics) == 1

    def test_cleanup(self):
        """Test collector cleanup"""
        collector = MetricsCollector()
        
        # Add some data
        with collector._buffer_lock:
            collector._metrics_buffer.append(PerformanceMetric(
                timestamp=datetime.now(),
                name="test",
                value=1.0,
                unit="test",
                metric_type=MetricType.GAUGE,
                source="test"
            ))
        
        collector.add_callback(lambda x: None)
        
        # Cleanup
        collector.cleanup()
        
        assert len(collector._sources) == 0
        assert len(collector._callbacks) == 0
        assert len(collector._metrics_buffer) == 0


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_record_response_time(self):
        """Test record_response_time convenience function"""
        # This will use the global collector
        record_response_time(100.0)
        
        collector = get_metrics_collector()
        app_source = collector._sources.get("application")
        
        if isinstance(app_source, ApplicationMetricsSource):
            assert len(app_source._response_times) > 0

    def test_record_request(self):
        """Test record_request convenience function"""
        record_request("/api/test")
        
        collector = get_metrics_collector()
        app_source = collector._sources.get("application")
        
        if isinstance(app_source, ApplicationMetricsSource):
            assert app_source._request_counts["/api/test"] > 0

    def test_record_error(self):
        """Test record_error convenience function"""
        record_error("TestError")
        
        collector = get_metrics_collector()
        app_source = collector._sources.get("application")
        
        if isinstance(app_source, ApplicationMetricsSource):
            assert app_source._error_counts["TestError"] > 0


if __name__ == "__main__":
    pytest.main([__file__])