"""
Tests for Metrics Collector

This module tests the comprehensive metric collection functionality including
system metrics, application metrics, and custom metric sources.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.core.metrics_collector import (
    MetricsCollector,
    MetricSource,
    SystemMetricsSource,
    ApplicationMetricsSource,
    CustomMetricsSource,
    PerformanceMetric,
    MetricType
)
from src.core.performance_monitor import MonitoringConfiguration


class MockMetricSource(MetricSource):
    """Mock metric source for testing."""
    
    def __init__(self, name: str, available: bool = True, metrics_count: int = 2):
        self.name = name
        self.available = available
        self.metrics_count = metrics_count
        self.cleanup_called = False
    
    def get_source_name(self) -> str:
        return self.name
    
    def collect_metrics(self) -> list:
        if not self.available:
            raise Exception("Source not available")
        
        metrics = []
        for i in range(self.metrics_count):
            metrics.append(PerformanceMetric(
                timestamp=datetime.now(),
                name=f"test_metric_{i}",
                value=float(i * 10),
                unit="test_unit",
                metric_type=MetricType.GAUGE,
                source=self.name,
                tags={"test": "true"},
                metadata={"index": i}
            ))
        return metrics
    
    def is_available(self) -> bool:
        return self.available
    
    def cleanup(self) -> None:
        self.cleanup_called = True


class TestPerformanceMetric:
    """Test performance metric data structure."""
    
    def test_metric_creation(self):
        """Test performance metric creation."""
        timestamp = datetime.now()
        metric = PerformanceMetric(
            timestamp=timestamp,
            name="test_metric",
            value=42.5,
            unit="percent",
            metric_type=MetricType.GAUGE,
            source="test_source",
            tags={"env": "test"},
            metadata={"description": "Test metric"}
        )
        
        assert metric.timestamp == timestamp
        assert metric.name == "test_metric"
        assert metric.value == 42.5
        assert metric.unit == "percent"
        assert metric.metric_type == MetricType.GAUGE
        assert metric.source == "test_source"
        assert metric.tags == {"env": "test"}
        assert metric.metadata == {"description": "Test metric"}


class TestSystemMetricsSource:
    """Test system metrics source."""
    
    @patch('src.core.metrics_collector.psutil')
    def test_system_source_initialization(self, mock_psutil):
        """Test system metrics source initialization."""
        source = SystemMetricsSource()
        
        assert source.get_source_name() == "system"
        assert source._last_cpu_times is None
        assert source._last_network_io is None
        assert source._last_disk_io is None
    
    @patch('src.core.metrics_collector.psutil')
    def test_system_source_availability(self, mock_psutil):
        """Test system metrics source availability check."""
        mock_psutil.cpu_percent.return_value = 50.0
        
        source = SystemMetricsSource()
        assert source.is_available() is True
        
        mock_psutil.cpu_percent.side_effect = Exception("CPU not available")
        assert source.is_available() is False
    
    @patch('src.core.metrics_collector.psutil')
    def test_collect_system_metrics(self, mock_psutil):
        """Test system metrics collection."""
        # Mock psutil functions
        mock_psutil.cpu_percent.return_value = 75.0
        mock_psutil.cpu_count.return_value = 4
        mock_psutil.cpu_freq.return_value = Mock(current=2400.0, max=3000.0, min=800.0)
        
        mock_memory = Mock()
        mock_memory.percent = 60.0
        mock_memory.total = 8 * 1024 * 1024 * 1024  # 8GB
        mock_memory.available = 3 * 1024 * 1024 * 1024  # 3GB
        mock_psutil.virtual_memory.return_value = mock_memory
        
        mock_swap = Mock()
        mock_swap.percent = 10.0
        mock_swap.total = 2 * 1024 * 1024 * 1024  # 2GB
        mock_psutil.swap_memory.return_value = mock_swap
        
        mock_disk_usage = Mock()
        mock_disk_usage.total = 100 * 1024 * 1024 * 1024  # 100GB
        mock_disk_usage.used = 50 * 1024 * 1024 * 1024   # 50GB
        mock_psutil.disk_usage.return_value = mock_disk_usage
        
        mock_psutil.disk_io_counters.return_value = None
        mock_psutil.net_io_counters.return_value = None
        
        source = SystemMetricsSource()
        metrics = source.collect_metrics()
        
        assert len(metrics) >= 5  # At least CPU, memory, swap, disk metrics
        
        # Check CPU metric
        cpu_metrics = [m for m in metrics if m.name == "cpu_usage_percent"]
        assert len(cpu_metrics) == 1
        assert cpu_metrics[0].value == 75.0
        assert cpu_metrics[0].unit == "percent"
        assert cpu_metrics[0].source == "system"
        
        # Check memory metric
        memory_metrics = [m for m in metrics if m.name == "memory_usage_percent"]
        assert len(memory_metrics) == 1
        assert memory_metrics[0].value == 60.0
    
    @patch('src.core.metrics_collector.psutil')
    def test_collect_system_metrics_with_rates(self, mock_psutil):
        """Test system metrics collection with rate calculations."""
        # Setup mocks for rate calculations
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.cpu_count.return_value = 2
        mock_psutil.cpu_freq.return_value = None
        mock_psutil.virtual_memory.return_value = Mock(percent=50.0, total=8*1024**3, available=4*1024**3)
        mock_psutil.swap_memory.return_value = Mock(percent=0.0, total=2*1024**3)
        mock_psutil.disk_usage.return_value = Mock(total=100*1024**3, used=50*1024**3)
        
        # Mock IO counters for rate calculation
        mock_disk_io_1 = Mock(read_bytes=1000, write_bytes=2000)
        mock_disk_io_2 = Mock(read_bytes=2000, write_bytes=4000)
        mock_psutil.disk_io_counters.side_effect = [mock_disk_io_1, mock_disk_io_2]
        
        mock_net_io_1 = Mock(bytes_sent=5000, bytes_recv=10000)
        mock_net_io_2 = Mock(bytes_sent=6000, bytes_recv=12000)
        mock_psutil.net_io_counters.side_effect = [mock_net_io_1, mock_net_io_2]
        
        source = SystemMetricsSource()
        
        # First collection to establish baseline
        metrics1 = source.collect_metrics()
        
        # Wait a bit and collect again
        time.sleep(0.1)
        metrics2 = source.collect_metrics()
        
        # Check that rate metrics are present in second collection
        rate_metrics = [m for m in metrics2 if "rate" in m.name]
        assert len(rate_metrics) >= 2  # Should have disk and network rates


class TestApplicationMetricsSource:
    """Test application metrics source."""
    
    def test_application_source_initialization(self):
        """Test application metrics source initialization."""
        source = ApplicationMetricsSource()
        
        assert source.get_source_name() == "application"
        assert source.is_available() is True
        assert len(source._response_times) == 0
        assert len(source._error_counts) == 0
        assert len(source._request_counts) == 0
    
    def test_record_response_time(self):
        """Test recording response times."""
        source = ApplicationMetricsSource()
        
        source.record_response_time(100.5)
        source.record_response_time(200.0)
        source.record_response_time(150.3)
        
        assert len(source._response_times) == 3
        assert 100.5 in source._response_times
        assert 200.0 in source._response_times
        assert 150.3 in source._response_times
    
    def test_record_requests_and_errors(self):
        """Test recording requests and errors."""
        source = ApplicationMetricsSource()
        
        source.record_request("/api/users")
        source.record_request("/api/users")
        source.record_request("/api/posts")
        
        source.record_error("/api/users", "404")
        source.record_error("/api/posts", "500")
        
        assert source._request_counts["/api/users"] == 2
        assert source._request_counts["/api/posts"] == 1
        assert source._error_counts["/api/users:404"] == 1
        assert source._error_counts["/api/posts:500"] == 1
    
    def test_collect_application_metrics(self):
        """Test application metrics collection."""
        source = ApplicationMetricsSource()
        
        # Record some data
        source.record_response_time(100.0)
        source.record_response_time(200.0)
        source.record_response_time(150.0)
        
        source.record_request("/api/test")
        source.record_request("/api/test")
        source.record_error("/api/test", "500")
        
        metrics = source.collect_metrics()
        
        # Check response time metrics
        avg_metrics = [m for m in metrics if m.name == "response_time_avg_ms"]
        assert len(avg_metrics) == 1
        assert avg_metrics[0].value == 150.0  # (100 + 200 + 150) / 3
        
        max_metrics = [m for m in metrics if m.name == "response_time_max_ms"]
        assert len(max_metrics) == 1
        assert max_metrics[0].value == 200.0
        
        min_metrics = [m for m in metrics if m.name == "response_time_min_ms"]
        assert len(min_metrics) == 1
        assert min_metrics[0].value == 100.0
        
        # Check error rate
        error_rate_metrics = [m for m in metrics if m.name == "error_rate_percent"]
        assert len(error_rate_metrics) == 1
        assert error_rate_metrics[0].value == 50.0  # 1 error out of 2 requests
        
        # Check that data is cleared after collection
        assert len(source._response_times) == 0
        assert len(source._request_counts) == 0
        assert len(source._error_counts) == 0
    
    def test_collect_metrics_no_data(self):
        """Test collecting metrics when no data is available."""
        source = ApplicationMetricsSource()
        metrics = source.collect_metrics()
        
        # Should still return throughput metric with 0 value
        throughput_metrics = [m for m in metrics if m.name == "requests_per_minute"]
        assert len(throughput_metrics) == 1
        assert throughput_metrics[0].value == 0


class TestCustomMetricsSource:
    """Test custom metrics source."""
    
    def test_custom_source_initialization(self):
        """Test custom metrics source initialization."""
        source = CustomMetricsSource("test_custom")
        
        assert source.get_source_name() == "custom_test_custom"
        assert source.is_available() is True
        assert len(source._metrics) == 0
    
    def test_add_and_collect_custom_metrics(self):
        """Test adding and collecting custom metrics."""
        source = CustomMetricsSource("test")
        
        metric1 = PerformanceMetric(
            timestamp=datetime.now(),
            name="custom_metric_1",
            value=42.0,
            unit="count",
            metric_type=MetricType.COUNTER,
            source="custom_test",
            tags={"custom": "true"},
            metadata={}
        )
        
        metric2 = PerformanceMetric(
            timestamp=datetime.now(),
            name="custom_metric_2",
            value=100.5,
            unit="percent",
            metric_type=MetricType.GAUGE,
            source="custom_test",
            tags={"custom": "true"},
            metadata={}
        )
        
        source.add_metric(metric1)
        source.add_metric(metric2)
        
        metrics = source.collect_metrics()
        
        assert len(metrics) == 2
        assert metrics[0].name == "custom_metric_1"
        assert metrics[1].name == "custom_metric_2"
        
        # Check that metrics are cleared after collection
        assert len(source._metrics) == 0


class TestMetricsCollector:
    """Test metrics collector functionality."""
    
    def test_collector_initialization(self):
        """Test metrics collector initialization."""
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        assert collector.config == config
        assert len(collector._sources) >= 1  # Should have at least application source
        assert "application" in collector._sources
    
    @patch('src.core.metrics_collector.SystemMetricsSource')
    def test_collector_initialization_with_system_source(self, mock_system_source):
        """Test collector initialization with system source."""
        mock_source_instance = Mock()
        mock_source_instance.is_available.return_value = True
        mock_system_source.return_value = mock_source_instance
        
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        assert "system" in collector._sources
        mock_system_source.assert_called_once()
    
    def test_register_source(self):
        """Test registering a new metric source."""
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        mock_source = MockMetricSource("test_source")
        result = collector.register_source(mock_source)
        
        assert result is True
        assert "test_source" in collector._sources
        assert collector._sources["test_source"] == mock_source
    
    def test_register_unavailable_source(self):
        """Test registering an unavailable source."""
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        mock_source = MockMetricSource("unavailable_source", available=False)
        result = collector.register_source(mock_source)
        
        assert result is False
        assert "unavailable_source" not in collector._sources
    
    def test_register_duplicate_source(self):
        """Test registering a source with duplicate name."""
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        mock_source1 = MockMetricSource("duplicate")
        mock_source2 = MockMetricSource("duplicate")
        
        result1 = collector.register_source(mock_source1)
        result2 = collector.register_source(mock_source2)
        
        assert result1 is True
        assert result2 is False
        assert collector._sources["duplicate"] == mock_source1
    
    def test_unregister_source(self):
        """Test unregistering a metric source."""
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        mock_source = MockMetricSource("test_source")
        collector.register_source(mock_source)
        
        result = collector.unregister_source("test_source")
        
        assert result is True
        assert "test_source" not in collector._sources
        assert mock_source.cleanup_called is True
    
    def test_unregister_nonexistent_source(self):
        """Test unregistering a non-existent source."""
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        result = collector.unregister_source("nonexistent")
        
        assert result is False
    
    def test_collect_all_metrics(self):
        """Test collecting metrics from all sources."""
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        # Add mock sources
        mock_source1 = MockMetricSource("source1", metrics_count=2)
        mock_source2 = MockMetricSource("source2", metrics_count=3)
        
        collector.register_source(mock_source1)
        collector.register_source(mock_source2)
        
        metrics = collector.collect_all_metrics()
        
        # Should have metrics from both sources plus application source
        assert len(metrics) >= 5  # 2 + 3 from mock sources, plus any from application
        
        # Check metric structure
        for metric in metrics:
            assert 'timestamp' in metric
            assert 'name' in metric
            assert 'value' in metric
            assert 'unit' in metric
            assert 'type' in metric
            assert 'source' in metric
            assert 'tags' in metric
            assert 'metadata' in metric
    
    def test_collect_metrics_from_specific_source(self):
        """Test collecting metrics from a specific source."""
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        mock_source = MockMetricSource("specific_source", metrics_count=3)
        collector.register_source(mock_source)
        
        metrics = collector.collect_metrics_from_source("specific_source")
        
        assert len(metrics) == 3
        for metric in metrics:
            assert metric['source'] == "specific_source"
    
    def test_collect_metrics_from_nonexistent_source(self):
        """Test collecting metrics from non-existent source."""
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        metrics = collector.collect_metrics_from_source("nonexistent")
        
        assert len(metrics) == 0
    
    def test_collect_metrics_from_unavailable_source(self):
        """Test collecting metrics from unavailable source."""
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        mock_source = MockMetricSource("unavailable", available=False)
        collector._sources["unavailable"] = mock_source  # Add directly to bypass availability check
        
        metrics = collector.collect_metrics_from_source("unavailable")
        
        assert len(metrics) == 0
    
    def test_get_active_sources_count(self):
        """Test getting active sources count."""
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        initial_count = collector.get_active_sources_count()
        
        # Add available source
        mock_source1 = MockMetricSource("available", available=True)
        collector.register_source(mock_source1)
        
        # Add unavailable source directly
        mock_source2 = MockMetricSource("unavailable", available=False)
        collector._sources["unavailable"] = mock_source2
        
        final_count = collector.get_active_sources_count()
        
        assert final_count == initial_count + 1  # Only the available source should be counted
    
    def test_get_source_names(self):
        """Test getting source names."""
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        mock_source = MockMetricSource("test_source")
        collector.register_source(mock_source)
        
        names = collector.get_source_names()
        
        assert "test_source" in names
        assert "application" in names
    
    def test_get_source_status(self):
        """Test getting source status."""
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        mock_source1 = MockMetricSource("available", available=True)
        mock_source2 = MockMetricSource("unavailable", available=False)
        
        collector.register_source(mock_source1)
        collector._sources["unavailable"] = mock_source2
        
        status = collector.get_source_status()
        
        assert status["available"] is True
        assert status["unavailable"] is False
        assert status["application"] is True
    
    def test_get_application_source(self):
        """Test getting application source."""
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        app_source = collector.get_application_source()
        
        assert app_source is not None
        assert isinstance(app_source, ApplicationMetricsSource)
    
    def test_create_custom_source(self):
        """Test creating custom source."""
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        custom_source = collector.create_custom_source("my_custom")
        
        assert isinstance(custom_source, CustomMetricsSource)
        assert custom_source.get_source_name() == "custom_my_custom"
        assert "custom_my_custom" in collector._sources
    
    def test_update_config(self):
        """Test updating collector configuration."""
        config1 = MonitoringConfiguration(collection_interval=5.0)
        collector = MetricsCollector(config1)
        
        config2 = MonitoringConfiguration(collection_interval=10.0)
        collector.update_config(config2)
        
        assert collector.config == config2
        assert collector.config.collection_interval == 10.0
    
    def test_cleanup(self):
        """Test collector cleanup."""
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        mock_source = MockMetricSource("test_source")
        collector.register_source(mock_source)
        
        collector.cleanup()
        
        assert len(collector._sources) == 0
        assert mock_source.cleanup_called is True
    
    def test_error_handling_in_collection(self):
        """Test error handling during metric collection."""
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        # Create a source that raises an exception
        mock_source = Mock()
        mock_source.get_source_name.return_value = "error_source"
        mock_source.is_available.return_value = True
        mock_source.collect_metrics.side_effect = Exception("Collection error")
        
        collector._sources["error_source"] = mock_source
        
        # Should not raise exception, should handle gracefully
        metrics = collector.collect_all_metrics()
        
        # Should still get metrics from other sources
        assert isinstance(metrics, list)


class TestMetricsCollectorIntegration:
    """Integration tests for metrics collector."""
    
    def test_end_to_end_metric_collection(self):
        """Test end-to-end metric collection workflow."""
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        # Get application source and record some data
        app_source = collector.get_application_source()
        if app_source:
            app_source.record_response_time(100.0)
            app_source.record_request("/test")
        
        # Create custom source and add metrics
        custom_source = collector.create_custom_source("integration_test")
        custom_metric = PerformanceMetric(
            timestamp=datetime.now(),
            name="integration_metric",
            value=42.0,
            unit="count",
            metric_type=MetricType.COUNTER,
            source="custom_integration_test",
            tags={"test": "integration"},
            metadata={}
        )
        custom_source.add_metric(custom_metric)
        
        # Collect all metrics
        metrics = collector.collect_all_metrics()
        
        # Verify we got metrics from multiple sources
        sources = set(metric['source'] for metric in metrics)
        assert len(sources) >= 2  # At least application and custom
        
        # Verify metric structure
        for metric in metrics:
            assert all(key in metric for key in [
                'timestamp', 'name', 'value', 'unit', 'type', 'source', 'tags', 'metadata'
            ])
    
    def test_concurrent_metric_collection(self):
        """Test concurrent access to metrics collector."""
        import threading
        
        config = MonitoringConfiguration()
        collector = MetricsCollector(config)
        
        results = []
        errors = []
        
        def collect_metrics():
            try:
                metrics = collector.collect_all_metrics()
                results.append(len(metrics))
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=collect_metrics)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        assert len(errors) == 0
        assert len(results) == 5