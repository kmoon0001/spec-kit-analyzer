"""
Performance Monitor Service for Therapy Compliance Analyzer

This module provides comprehensive performance monitoring with real-time metric
collection, historical analysis, and intelligent insights.
"""

import logging
import threading
import time
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class MonitoringState(Enum):
    """Performance monitoring states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class MonitoringConfiguration:
    """Configuration for performance monitoring."""
    collection_interval: float = 5.0  # seconds
    retention_days: int = 30
    max_metrics_per_batch: int = 1000
    enable_real_time_alerts: bool = True
    enable_predictive_analysis: bool = True
    enable_benchmarking: bool = False
    storage_path: str = "data/monitoring"
    log_level: str = "INFO"
    
    # Alert thresholds
    cpu_threshold: float = 80.0
    memory_threshold: float = 85.0
    response_time_threshold: float = 2000.0  # milliseconds
    error_rate_threshold: float = 5.0  # percentage
    
    # Analytics settings
    trend_analysis_window: int = 24  # hours
    anomaly_detection_sensitivity: float = 2.0  # standard deviations
    prediction_horizon: int = 6  # hours


@dataclass
class MonitoringStatus:
    """Current monitoring system status."""
    state: MonitoringState
    uptime: timedelta
    metrics_collected: int
    alerts_generated: int
    last_collection: Optional[datetime]
    active_sources: int
    storage_usage_mb: float
    error_count: int
    last_error: Optional[str]


class PerformanceMonitor:
    """Central performance monitoring service."""
    
    def __init__(self, config: Optional[MonitoringConfiguration] = None):
        """Initialize performance monitor.
        
        Args:
            config: Monitoring configuration, uses defaults if None
        """
        self.config = config or MonitoringConfiguration()
        self.state = MonitoringState.STOPPED
        self.start_time: Optional[datetime] = None
        
        # Core components (will be initialized when needed)
        self.metrics_collector = None
        self.data_aggregator = None
        self.analytics_agent = None
        self.alert_router = None
        
        # Threading and synchronization
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()
        
        # Status tracking
        self._metrics_collected = 0
        self._alerts_generated = 0
        self._error_count = 0
        self._last_error: Optional[str] = None
        self._last_collection: Optional[datetime] = None
        
        # Callbacks for monitoring events
        self._status_callbacks: List[Callable[[MonitoringStatus], None]] = []
        self._metric_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
        # Ensure storage directory exists
        Path(self.config.storage_path).mkdir(parents=True, exist_ok=True)
        
        logger.info("Performance monitor initialized")
    
    def start_monitoring(self) -> bool:
        """Start the performance monitoring system.
        
        Returns:
            True if monitoring started successfully, False otherwise
        """
        with self._lock:
            if self.state in [MonitoringState.RUNNING, MonitoringState.STARTING]:
                logger.warning("Monitoring is already running or starting")
                return True
            
            if self.state == MonitoringState.STOPPING:
                logger.warning("Cannot start monitoring while stopping")
                return False
            
            self.state = MonitoringState.STARTING
            logger.info("Starting performance monitoring system")
        
        try:
            # Initialize core components
            self._initialize_components()
            
            # Start monitoring thread
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                name="PerformanceMonitor",
                daemon=True
            )
            self._monitor_thread.start()
            
            # Update state
            with self._lock:
                self.state = MonitoringState.RUNNING
                self.start_time = datetime.now()
                self._error_count = 0
                self._last_error = None
            
            logger.info("Performance monitoring started successfully")
            self._notify_status_change()
            return True
            
        except Exception as e:
            error_msg = f"Failed to start monitoring: {e}"
            logger.error(error_msg)
            
            with self._lock:
                self.state = MonitoringState.ERROR
                self._error_count += 1
                self._last_error = error_msg
            
            self._notify_status_change()
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop the performance monitoring system.
        
        Returns:
            True if monitoring stopped successfully, False otherwise
        """
        with self._lock:
            if self.state == MonitoringState.STOPPED:
                logger.info("Monitoring is already stopped")
                return True
            
            if self.state == MonitoringState.STOPPING:
                logger.info("Monitoring is already stopping")
                return True
            
            self.state = MonitoringState.STOPPING
            logger.info("Stopping performance monitoring system")
        
        try:
            # Signal monitoring thread to stop
            self._stop_event.set()
            
            # Wait for monitoring thread to finish
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=10.0)
                
                if self._monitor_thread.is_alive():
                    logger.warning("Monitoring thread did not stop gracefully")
            
            # Cleanup components
            self._cleanup_components()
            
            # Update state
            with self._lock:
                self.state = MonitoringState.STOPPED
                self.start_time = None
            
            logger.info("Performance monitoring stopped successfully")
            self._notify_status_change()
            return True
            
        except Exception as e:
            error_msg = f"Error stopping monitoring: {e}"
            logger.error(error_msg)
            
            with self._lock:
                self.state = MonitoringState.ERROR
                self._error_count += 1
                self._last_error = error_msg
            
            self._notify_status_change()
            return False
    
    def get_status(self) -> MonitoringStatus:
        """Get current monitoring system status.
        
        Returns:
            Current monitoring status
        """
        with self._lock:
            uptime = (datetime.now() - self.start_time) if self.start_time else timedelta()
            
            # Calculate storage usage (simplified)
            storage_usage_mb = 0.0
            try:
                storage_path = Path(self.config.storage_path)
                if storage_path.exists():
                    storage_usage_mb = sum(
                        f.stat().st_size for f in storage_path.rglob('*') if f.is_file()
                    ) / (1024 * 1024)
            except Exception:
                pass  # Ignore storage calculation errors
            
            return MonitoringStatus(
                state=self.state,
                uptime=uptime,
                metrics_collected=self._metrics_collected,
                alerts_generated=self._alerts_generated,
                last_collection=self._last_collection,
                active_sources=self._get_active_sources_count(),
                storage_usage_mb=storage_usage_mb,
                error_count=self._error_count,
                last_error=self._last_error
            )
    
    def configure_monitoring(self, config: MonitoringConfiguration) -> bool:
        """Update monitoring configuration.
        
        Args:
            config: New monitoring configuration
            
        Returns:
            True if configuration updated successfully, False otherwise
        """
        try:
            with self._lock:
                old_config = self.config
                self.config = config
                
                # Ensure storage directory exists
                Path(self.config.storage_path).mkdir(parents=True, exist_ok=True)
                
                # If monitoring is running, apply configuration changes
                if self.state == MonitoringState.RUNNING:
                    self._apply_configuration_changes(old_config, config)
            
            logger.info("Monitoring configuration updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update monitoring configuration: {e}")
            return False
    
    def add_status_callback(self, callback: Callable[[MonitoringStatus], None]) -> None:
        """Add callback for monitoring status changes.
        
        Args:
            callback: Function to call when status changes
        """
        with self._lock:
            self._status_callbacks.append(callback)
    
    def remove_status_callback(self, callback: Callable[[MonitoringStatus], None]) -> None:
        """Remove status change callback.
        
        Args:
            callback: Function to remove from callbacks
        """
        with self._lock:
            if callback in self._status_callbacks:
                self._status_callbacks.remove(callback)
    
    def add_metric_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Add callback for new metrics.
        
        Args:
            callback: Function to call when new metrics are collected
        """
        with self._lock:
            self._metric_callbacks.append(callback)
    
    def export_configuration(self, file_path: str) -> bool:
        """Export current configuration to YAML file.
        
        Args:
            file_path: Path to save configuration file
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            config_dict = asdict(self.config)
            
            with open(file_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration exported to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_configuration(self, file_path: str) -> bool:
        """Import configuration from YAML file.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            True if import successful, False otherwise
        """
        try:
            with open(file_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            
            config = MonitoringConfiguration(**config_dict)
            return self.configure_monitoring(config)
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False
    
    def _initialize_components(self) -> None:
        """Initialize monitoring components."""
        # Import here to avoid circular imports
        from .metrics_collector import MetricsCollector
        from .data_aggregator import DataAggregator
        
        # Initialize components
        self.metrics_collector = MetricsCollector(self.config)
        self.data_aggregator = DataAggregator(self.config)
        
        # Initialize optional components based on configuration
        if self.config.enable_predictive_analysis:
            try:
                from .analytics_agent import AnalyticsAgent
                self.analytics_agent = AnalyticsAgent(self.config)
            except ImportError:
                logger.warning("Analytics agent not available, predictive analysis disabled")
        
        if self.config.enable_real_time_alerts:
            try:
                from .alert_router import AlertRouter
                self.alert_router = AlertRouter(self.config)
            except ImportError:
                logger.warning("Alert router not available, real-time alerts disabled")
        
        logger.debug("Monitoring components initialized")
    
    def _cleanup_components(self) -> None:
        """Cleanup monitoring components."""
        components = [
            self.metrics_collector,
            self.data_aggregator,
            self.analytics_agent,
            self.alert_router
        ]
        
        for component in components:
            if component and hasattr(component, 'cleanup'):
                try:
                    component.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up component {component}: {e}")
        
        # Clear component references
        self.metrics_collector = None
        self.data_aggregator = None
        self.analytics_agent = None
        self.alert_router = None
        
        logger.debug("Monitoring components cleaned up")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        logger.info("Monitoring loop started")
        
        while not self._stop_event.is_set():
            try:
                loop_start = time.time()
                
                # Collect metrics
                if self.metrics_collector:
                    metrics = self.metrics_collector.collect_all_metrics()
                    
                    if metrics:
                        # Update collection stats
                        with self._lock:
                            self._metrics_collected += len(metrics)
                            self._last_collection = datetime.now()
                        
                        # Process metrics
                        if self.data_aggregator:
                            self.data_aggregator.process_metrics(metrics)
                        
                        # Notify metric callbacks
                        self._notify_metric_callbacks(metrics)
                
                # Calculate sleep time to maintain collection interval
                loop_duration = time.time() - loop_start
                sleep_time = max(0, self.config.collection_interval - loop_duration)
                
                if sleep_time > 0:
                    self._stop_event.wait(sleep_time)
                else:
                    logger.warning(f"Monitoring loop took {loop_duration:.2f}s, "
                                 f"longer than interval {self.config.collection_interval}s")
                
            except Exception as e:
                error_msg = f"Error in monitoring loop: {e}"
                logger.error(error_msg)
                
                with self._lock:
                    self._error_count += 1
                    self._last_error = error_msg
                
                # Brief pause before retrying
                self._stop_event.wait(1.0)
        
        logger.info("Monitoring loop stopped")
    
    def _apply_configuration_changes(self, old_config: MonitoringConfiguration, 
                                   new_config: MonitoringConfiguration) -> None:
        """Apply configuration changes to running components."""
        # Update component configurations if they exist
        if self.metrics_collector and hasattr(self.metrics_collector, 'update_config'):
            self.metrics_collector.update_config(new_config)
        
        if self.data_aggregator and hasattr(self.data_aggregator, 'update_config'):
            self.data_aggregator.update_config(new_config)
        
        if self.analytics_agent and hasattr(self.analytics_agent, 'update_config'):
            self.analytics_agent.update_config(new_config)
        
        if self.alert_router and hasattr(self.alert_router, 'update_config'):
            self.alert_router.update_config(new_config)
        
        logger.debug("Configuration changes applied to components")
    
    def _get_active_sources_count(self) -> int:
        """Get count of active metric sources."""
        if self.metrics_collector and hasattr(self.metrics_collector, 'get_active_sources_count'):
            return self.metrics_collector.get_active_sources_count()
        return 0
    
    def _notify_status_change(self) -> None:
        """Notify all status callbacks of status change."""
        status = self.get_status()
        
        for callback in self._status_callbacks:
            try:
                callback(status)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")
    
    def _notify_metric_callbacks(self, metrics: List[Dict[str, Any]]) -> None:
        """Notify all metric callbacks of new metrics."""
        for callback in self._metric_callbacks:
            try:
                for metric in metrics:
                    callback(metric)
            except Exception as e:
                logger.error(f"Error in metric callback: {e}")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()