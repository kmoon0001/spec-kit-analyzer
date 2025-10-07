"""
Tests for Performance Monitor Service

This module tests the core performance monitoring functionality including
lifecycle management, configuration, and status tracking.
"""

import pytest
import time
import tempfile
import yaml
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path

from src.core.performance_monitor import (
    PerformanceMonitor,
    MonitoringConfiguration,
    MonitoringStatus,
    MonitoringState,
    performance_monitor
)


class TestMonitoringConfiguration:
    """Test monitoring configuration."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = MonitoringConfiguration()
        
        assert config.collection_interval == 5.0
        assert config.retention_days == 30
        assert config.max_metrics_per_batch == 1000
        assert config.enable_real_time_alerts is True
        assert config.enable_predictive_analysis is True
        assert config.enable_benchmarking is False
        assert config.storage_path == "data/monitoring"
        assert config.log_level == "INFO"
        
        # Alert thresholds
        assert config.cpu_threshold == 80.0
        assert config.memory_threshold == 85.0
        assert config.response_time_threshold == 2000.0
        assert config.error_rate_threshold == 5.0
        
        # Analytics settings
        assert config.trend_analysis_window == 24
        assert config.anomaly_detection_sensitivity == 2.0
        assert config.prediction_horizon == 6
    
    def test_custom_configuration(self):
        """Test custom configuration values."""
        config = MonitoringConfiguration(
            collection_interval=10.0,
            retention_days=60,
            max_metrics_per_batch=500,
            enable_real_time_alerts=False,
            cpu_threshold=90.0,
            storage_path="custom/path"
        )
        
        assert config.collection_interval == 10.0
        assert config.retention_days == 60
        assert config.max_metrics_per_batch == 500
        assert config.enable_real_time_alerts is False
        assert config.cpu_threshold == 90.0
        assert config.storage_path == "custom/path"


class TestMonitoringStatus:
    """Test monitoring status data structure."""
    
    def test_status_creation(self):
        """Test monitoring status creation."""
        status = MonitoringStatus(
            state=MonitoringState.RUNNING,
            uptime=timedelta(hours=2),
            metrics_collected=1000,
            alerts_generated=5,
            last_collection=datetime.now(),
            active_sources=3,
            storage_usage_mb=50.5,
            error_count=2,
            last_error="Test error"
        )
        
        assert status.state == MonitoringState.RUNNING
        assert status.uptime == timedelta(hours=2)
        assert status.metrics_collected == 1000
        assert status.alerts_generated == 5
        assert status.active_sources == 3
        assert status.storage_usage_mb == 50.5
        assert status.error_count == 2
        assert status.last_error == "Test error"


class TestPerformanceMonitor:
    """Test performance monitor functionality."""
    
    def test_monitor_initialization(self):
        """Test performance monitor initialization."""
        config = MonitoringConfiguration(storage_path="test/monitoring")
        monitor = PerformanceMonitor(config)
        
        assert monitor.config == config
        assert monitor.state == MonitoringState.STOPPED
        assert monitor.start_time is None
        assert monitor._metrics_collected == 0
        assert monitor._alerts_generated == 0
        assert monitor._error_count == 0
        assert monitor._last_error is None
    
    def test_monitor_initialization_with_defaults(self):
        """Test performance monitor initialization with default config."""
        monitor = PerformanceMonitor()
        
        assert isinstance(monitor.config, MonitoringConfiguration)
        assert monitor.state == MonitoringState.STOPPED
        assert monitor.config.collection_interval == 5.0
    
    @patch('src.core.performance_monitor.Path')
    def test_storage_directory_creation(self, mock_path):
        """Test storage directory creation during initialization."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        
        config = MonitoringConfiguration(storage_path="test/path")
        PerformanceMonitor(config)
        
        mock_path.assert_called_with("test/path")
        mock_path_instance.mkdir.assert_called_with(parents=True, exist_ok=True)
    
    def test_get_status_when_stopped(self):
        """Test getting status when monitoring is stopped."""
        monitor = PerformanceMonitor()
        status = monitor.get_status()
        
        assert status.state == MonitoringState.STOPPED
        assert status.uptime == timedelta()
        assert status.metrics_collected == 0
        assert status.alerts_generated == 0
        assert status.last_collection is None
        assert status.active_sources == 0
        assert status.error_count == 0
        assert status.last_error is None
    
    @patch('src.core.performance_monitor.PerformanceMonitor._initialize_components')
    @patch('threading.Thread')
    def test_start_monitoring_success(self, mock_thread, mock_init):
        """Test successful monitoring start."""
        monitor = PerformanceMonitor()
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        result = monitor.start_monitoring()
        
        assert result is True
        assert monitor.state == MonitoringState.RUNNING
        assert monitor.start_time is not None
        mock_init.assert_called_once()
        mock_thread_instance.start.assert_called_once()
    
    def test_start_monitoring_already_running(self):
        """Test starting monitoring when already running."""
        monitor = PerformanceMonitor()
        monitor.state = MonitoringState.RUNNING
        
        result = monitor.start_monitoring()
        
        assert result is True
        assert monitor.state == MonitoringState.RUNNING
    
    def test_start_monitoring_while_stopping(self):
        """Test starting monitoring while stopping."""
        monitor = PerformanceMonitor()
        monitor.state = MonitoringState.STOPPING
        
        result = monitor.start_monitoring()
        
        assert result is False
        assert monitor.state == MonitoringState.STOPPING
    
    @patch('src.core.performance_monitor.PerformanceMonitor._initialize_components')
    def test_start_monitoring_initialization_failure(self, mock_init):
        """Test monitoring start with initialization failure."""
        monitor = PerformanceMonitor()
        mock_init.side_effect = Exception("Initialization failed")
        
        result = monitor.start_monitoring()
        
        assert result is False
        assert monitor.state == MonitoringState.ERROR
        assert monitor._error_count == 1
        assert "Initialization failed" in monitor._last_error
    
    def test_stop_monitoring_when_stopped(self):
        """Test stopping monitoring when already stopped."""
        monitor = PerformanceMonitor()
        
        result = monitor.stop_monitoring()
        
        assert result is True
        assert monitor.state == MonitoringState.STOPPED
    
    def test_stop_monitoring_when_stopping(self):
        """Test stopping monitoring when already stopping."""
        monitor = PerformanceMonitor()
        monitor.state = MonitoringState.STOPPING
        
        result = monitor.stop_monitoring()
        
        assert result is True
        assert monitor.state == MonitoringState.STOPPING
    
    @patch('src.core.performance_monitor.PerformanceMonitor._cleanup_components')
    def test_stop_monitoring_success(self, mock_cleanup):
        """Test successful monitoring stop."""
        monitor = PerformanceMonitor()
        monitor.state = MonitoringState.RUNNING
        monitor.start_time = datetime.now()
        
        # Mock thread
        mock_thread = Mock()
        mock_thread.is_alive.return_value = False
        monitor._monitor_thread = mock_thread
        
        result = monitor.stop_monitoring()
        
        assert result is True
        assert monitor.state == MonitoringState.STOPPED
        assert monitor.start_time is None
        mock_cleanup.assert_called_once()
    
    @patch('src.core.performance_monitor.PerformanceMonitor._cleanup_components')
    def test_stop_monitoring_thread_timeout(self, mock_cleanup):
        """Test monitoring stop with thread timeout."""
        monitor = PerformanceMonitor()
        monitor.state = MonitoringState.RUNNING
        
        # Mock thread that doesn't stop
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        monitor._monitor_thread = mock_thread
        
        result = monitor.stop_monitoring()
        
        assert result is True
        assert monitor.state == MonitoringState.STOPPED
        mock_thread.join.assert_called_with(timeout=10.0)
    
    def test_configure_monitoring(self):
        """Test monitoring configuration update."""
        monitor = PerformanceMonitor()
        new_config = MonitoringConfiguration(
            collection_interval=10.0,
            retention_days=60
        )
        
        result = monitor.configure_monitoring(new_config)
        
        assert result is True
        assert monitor.config == new_config
        assert monitor.config.collection_interval == 10.0
        assert monitor.config.retention_days == 60
    
    @patch('src.core.performance_monitor.Path')
    def test_configure_monitoring_storage_creation(self, mock_path):
        """Test storage directory creation during configuration update."""
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        
        monitor = PerformanceMonitor()
        new_config = MonitoringConfiguration(storage_path="new/path")
        
        monitor.configure_monitoring(new_config)
        
        mock_path.assert_called_with("new/path")
        mock_path_instance.mkdir.assert_called_with(parents=True, exist_ok=True)
    
    def test_status_callbacks(self):
        """Test status change callbacks."""
        monitor = PerformanceMonitor()
        callback1 = Mock()
        callback2 = Mock()
        
        # Add callbacks
        monitor.add_status_callback(callback1)
        monitor.add_status_callback(callback2)
        
        # Trigger status change
        monitor._notify_status_change()
        
        callback1.assert_called_once()
        callback2.assert_called_once()
        
        # Remove callback
        monitor.remove_status_callback(callback1)
        monitor._notify_status_change()
        
        # callback1 should not be called again, callback2 should be called twice
        assert callback1.call_count == 1
        assert callback2.call_count == 2
    
    def test_metric_callbacks(self):
        """Test metric callbacks."""
        monitor = PerformanceMonitor()
        callback = Mock()
        
        monitor.add_metric_callback(callback)
        
        # Simulate metrics
        metrics = [
            {'name': 'cpu_usage', 'value': 50.0},
            {'name': 'memory_usage', 'value': 60.0}
        ]
        
        monitor._notify_metric_callbacks(metrics)
        
        assert callback.call_count == 2
        callback.assert_any_call({'name': 'cpu_usage', 'value': 50.0})
        callback.assert_any_call({'name': 'memory_usage', 'value': 60.0})
    
    def test_callback_error_handling(self):
        """Test error handling in callbacks."""
        monitor = PerformanceMonitor()
        
        # Create callback that raises exception
        error_callback = Mock(side_effect=Exception("Callback error"))
        good_callback = Mock()
        
        monitor.add_status_callback(error_callback)
        monitor.add_status_callback(good_callback)
        
        # Should not raise exception
        monitor._notify_status_change()
        
        # Good callback should still be called
        good_callback.assert_called_once()
    
    def test_export_configuration(self):
        """Test configuration export to YAML."""
        monitor = PerformanceMonitor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            result = monitor.export_configuration(temp_path)
            
            assert result is True
            
            # Verify file contents
            with open(temp_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            assert config_data['collection_interval'] == 5.0
            assert config_data['retention_days'] == 30
            assert config_data['enable_real_time_alerts'] is True
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_import_configuration(self):
        """Test configuration import from YAML."""
        monitor = PerformanceMonitor()
        
        config_data = {
            'collection_interval': 15.0,
            'retention_days': 45,
            'enable_real_time_alerts': False,
            'cpu_threshold': 95.0
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            result = monitor.import_configuration(temp_path)
            
            assert result is True
            assert monitor.config.collection_interval == 15.0
            assert monitor.config.retention_days == 45
            assert monitor.config.enable_real_time_alerts is False
            assert monitor.config.cpu_threshold == 95.0
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_import_configuration_invalid_file(self):
        """Test configuration import with invalid file."""
        monitor = PerformanceMonitor()
        
        result = monitor.import_configuration("nonexistent_file.yaml")
        
        assert result is False


class TestPerformanceMonitorIntegration:
    """Integration tests for performance monitor."""
    
    @patch('src.core.metrics_collector.MetricsCollector')
    @patch('src.core.data_aggregator.DataAggregator')
    def test_component_initialization(self, mock_aggregator, mock_collector):
        """Test component initialization during startup."""
        monitor = PerformanceMonitor()
        
        # Mock component classes
        mock_collector_instance = Mock()
        mock_aggregator_instance = Mock()
        mock_collector.return_value = mock_collector_instance
        mock_aggregator.return_value = mock_aggregator_instance
        
        monitor._initialize_components()
        
        assert monitor.metrics_collector == mock_collector_instance
        assert monitor.data_aggregator == mock_aggregator_instance
        mock_collector.assert_called_once_with(monitor.config)
        mock_aggregator.assert_called_once_with(monitor.config)
    
    def test_component_cleanup(self):
        """Test component cleanup during shutdown."""
        monitor = PerformanceMonitor()
        
        # Mock components with cleanup methods
        mock_collector = Mock()
        mock_aggregator = Mock()
        mock_collector.cleanup = Mock()
        mock_aggregator.cleanup = Mock()
        
        monitor.metrics_collector = mock_collector
        monitor.data_aggregator = mock_aggregator
        
        monitor._cleanup_components()
        
        mock_collector.cleanup.assert_called_once()
        mock_aggregator.cleanup.assert_called_once()
        assert monitor.metrics_collector is None
        assert monitor.data_aggregator is None
    
    def test_component_cleanup_error_handling(self):
        """Test error handling during component cleanup."""
        monitor = PerformanceMonitor()
        
        # Mock component that raises exception during cleanup
        mock_component = Mock()
        mock_component.cleanup.side_effect = Exception("Cleanup error")
        monitor.metrics_collector = mock_component
        
        # Should not raise exception
        monitor._cleanup_components()
        
        assert monitor.metrics_collector is None
    
    def test_get_active_sources_count(self):
        """Test getting active sources count."""
        monitor = PerformanceMonitor()
        
        # Mock metrics collector with active sources
        mock_collector = Mock()
        mock_collector.get_active_sources_count.return_value = 5
        monitor.metrics_collector = mock_collector
        
        count = monitor._get_active_sources_count()
        
        assert count == 5
        mock_collector.get_active_sources_count.assert_called_once()
    
    def test_get_active_sources_count_no_collector(self):
        """Test getting active sources count when no collector exists."""
        monitor = PerformanceMonitor()
        monitor.metrics_collector = None
        
        count = monitor._get_active_sources_count()
        
        assert count == 0


class TestGlobalPerformanceMonitor:
    """Test global performance monitor instance."""
    
    def test_global_instance_exists(self):
        """Test that global performance monitor instance exists."""
        assert performance_monitor is not None
        assert isinstance(performance_monitor, PerformanceMonitor)
    
    def test_global_instance_default_config(self):
        """Test that global instance has default configuration."""
        assert isinstance(performance_monitor.config, MonitoringConfiguration)
        assert performance_monitor.state == MonitoringState.STOPPED