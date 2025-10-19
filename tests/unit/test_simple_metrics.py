"""Simple test to verify testing infrastructure works."""

import pytest
from src.core.performance_metrics_collector import MetricsCollector


def test_metrics_collector_basic():
    """Test basic metrics collector functionality."""
    collector = MetricsCollector(max_history=10)

    # Test request recording
    collector.record_request(150.5, 200, "/test")

    current = collector.get_current_metrics()
    assert current.request_count == 1
    assert current.request_duration_ms == 150.5
    assert current.error_count == 0


def test_metrics_collector_error_recording():
    """Test error request recording."""
    collector = MetricsCollector(max_history=10)

    # Test error request
    collector.record_request(200.0, 400, "/test")

    current = collector.get_current_metrics()
    assert current.request_count == 1
    assert current.error_count == 1


def test_metrics_collector_database_queries():
    """Test database query recording."""
    collector = MetricsCollector(max_history=10)

    collector.record_database_query(50.0, "SELECT")

    current = collector.get_current_metrics()
    assert current.database_query_count == 1
    assert current.database_query_duration_ms == 50.0


def test_metrics_collector_ai_inference():
    """Test AI inference recording."""
    collector = MetricsCollector(max_history=10)

    collector.record_ai_inference(1000.0, "llama")

    current = collector.get_current_metrics()
    assert current.ai_inference_count == 1
    assert current.ai_inference_duration_ms == 1000.0


def test_metrics_collector_custom_metrics():
    """Test custom metrics recording."""
    collector = MetricsCollector(max_history=10)

    collector.record_custom_metric("test_metric", 42.5, {"tag": "value"})

    assert "test_metric" in collector.custom_metrics
    assert len(collector.custom_metrics["test_metric"]) == 1
    assert collector.custom_metrics["test_metric"][0].value == 42.5


def test_metrics_collector_reset():
    """Test metrics reset functionality."""
    collector = MetricsCollector(max_history=10)

    # Record some metrics
    collector.record_request(100.0, 200, "/test")
    collector.record_custom_metric("test", 42.0)

    # Reset
    collector.reset_metrics()

    current = collector.get_current_metrics()
    assert current.request_count == 0
    assert len(collector.custom_metrics) == 0


def test_metrics_summary_calculation():
    """Test metrics summary calculation."""
    collector = MetricsCollector(max_history=10)

    # Record some metrics
    collector.record_request(100.0, 200, "/test")
    collector.record_request(200.0, 200, "/test")
    collector.record_request(300.0, 400, "/test")  # Error

    summary = collector.get_metrics_summary()

    assert summary["requests"]["total"] == 3
    assert summary["requests"]["avg_duration_ms"] == 200.0
    assert summary["requests"]["error_count"] == 1
    assert summary["requests"]["error_rate_percent"] == 33.33
