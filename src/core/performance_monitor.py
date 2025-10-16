"""Performance Monitoring System

Comprehensive performance monitoring and metrics collection for all system components.
Provides real-time insights into system health, performance bottlenecks, and optimization opportunities.
"""

import logging
import os
import threading
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.metrics_collector import MetricsCollector
    from src.core.data_aggregator import DataAggregator

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)


class MonitoringState(Enum):
    """Monitoring system states."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class MonitoringConfiguration:
    """Configuration for performance monitoring."""

    # Basic settings
    enabled: bool = True
    collection_interval: float = 5.0
    retention_days: int = 30
    max_metrics_per_batch: int = 1000
    max_metrics_history: int = 10000
    storage_path: str = "data/monitoring"
    log_level: str = "INFO"

    # Feature flags
    enable_real_time_alerts: bool = True
    enable_predictive_analysis: bool = True
    enable_benchmarking: bool = False

    # Alert thresholds
    cpu_threshold: float = 80.0
    memory_threshold: float = 85.0
    response_time_threshold: float = 2000.0
    error_rate_threshold: float = 5.0

    # Analytics settings
    trend_analysis_window: int = 24
    anomaly_detection_sensitivity: float = 2.0
    prediction_horizon: int = 6

    # Legacy compatibility
    alert_thresholds: dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringStatus:
    """Current monitoring status."""

    state: MonitoringState
    uptime: timedelta
    metrics_collected: int
    alerts_generated: int
    last_collection: datetime | None
    active_sources: int
    storage_usage_mb: float
    error_count: int
    last_error: str | None


@dataclass
class PerformanceMetric:
    """Individual performance metric data point."""

    timestamp: datetime
    component: str
    operation: str
    duration_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success: bool
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """System health snapshot."""

    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_threads: int
    response_time_avg: float
    error_rate: float
    throughput: float


class PerformanceMonitor:
    """Comprehensive performance monitoring system.

    This system provides:
    - Real-time performance metrics collection
    - System health monitoring and alerting
    - Performance trend analysis and reporting
    - Bottleneck identification and optimization suggestions
    - Resource usage tracking and optimization

    Features:
    - Component-level performance tracking
    - Memory and CPU usage monitoring
    - Response time analysis
    - Error rate tracking
    - Throughput measurement
    - Performance alerts and notifications

    Example:
        >>> monitor = PerformanceMonitor()
        >>> with monitor.track_operation("pdf_export", "generate_report"):
        ...     generate_pdf_report()
        >>> health = monitor.get_system_health()
        >>> print(f"System health: {health.cpu_usage}% CPU")

    """

    def __init__(self, config: MonitoringConfiguration | None = None):
        """Initialize the performance monitoring system."""
        self.config = config or MonitoringConfiguration()
        self.max_metrics_history = self.config.max_metrics_history
        self.metrics_history: deque = deque(maxlen=self.max_metrics_history)
        self.component_metrics: dict[str, list[PerformanceMetric]] = defaultdict(list)
        self.active_operations: dict[str, dict[str, Any]] = {}
        self.performance_thresholds = self._initialize_thresholds()
        self.alerts_enabled = True
        self.monitoring_active = True

        # State management
        self.state = MonitoringState.STOPPED
        self._start_time = time.time()
        self._last_error: str | None = None
        self._monitor_thread: threading.Thread | None = None
        self._status_callbacks: list[Callable] = []
        self._metric_callbacks: list[Callable] = []

        # Test-expected attributes
        self.start_time: datetime | None = None
        self._metrics_collected: int = 0
        self._alerts_generated: int = 0
        self._error_count: int = 0

        # Components
        self.metrics_collector: "MetricsCollector | None" = None
        self.data_aggregator: "DataAggregator | None" = None

        # Create storage directory if needed
        if self.config.storage_path:
            storage_path = Path(self.config.storage_path)
            storage_path.mkdir(parents=True, exist_ok=True)

        logger.info("Performance monitoring system initialized")

    def track_operation(self, component: str, operation: str, metadata: dict[str, Any] | None = None):
        """Context manager for tracking operation performance.

        Args:
            component: Component name (e.g., "pdf_export", "ai_analysis")
            operation: Operation name (e.g., "generate_report", "analyze_document")
            metadata: Additional metadata to track

        Example:
            >>> with monitor.track_operation("ai_analysis", "compliance_check"):
            ...     result = analyze_compliance(document)

        """
        return OperationTracker(self, component, operation, metadata or {})

    async def track_async_operation(self, component: str, operation: str, func: Callable, *args, **kwargs) -> Any:
        """Track an async operation and return its result.

        Args:
            component: Component name
            operation: Operation name
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Result of the function execution

        """
        start_time = time.time()
        start_memory = self._get_memory_usage()
        start_cpu = self._get_cpu_usage()
        operation_id = str(uuid.uuid4())

        # Track active operation
        self.active_operations[operation_id] = {
            "component": component,
            "operation": operation,
            "start_time": start_time,
            "start_memory": start_memory,
        }

        try:
            result = await func(*args, **kwargs)
            success = True
            return result

        except Exception:
            success = False
            raise

        finally:
            # Calculate metrics
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            end_memory = self._get_memory_usage()
            end_cpu = self._get_cpu_usage()

            # Create metric
            metric = PerformanceMetric(
                timestamp=datetime.now(),
                component=component,
                operation=operation,
                duration_ms=duration_ms,
                memory_usage_mb=end_memory - start_memory,
                cpu_usage_percent=(end_cpu + start_cpu) / 2,
                success=success,
                metadata=kwargs.get("metadata", {}),
            )

            # Store metric
            self._store_metric(metric)

            # Remove from active operations
            if operation_id in self.active_operations:
                del self.active_operations[operation_id]

    def record_metric(
        self,
        component: str,
        operation: str,
        duration_ms: float,
        success: bool = True,
        metadata: dict[str, Any] | None = None,
    ):
        """Manually record a performance metric.

        Args:
            component: Component name
            operation: Operation name
            duration_ms: Operation duration in milliseconds
            success: Whether the operation was successful
            metadata: Additional metadata

        """
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            component=component,
            operation=operation,
            duration_ms=duration_ms,
            memory_usage_mb=self._get_memory_usage(),
            cpu_usage_percent=self._get_cpu_usage(),
            success=success,
            metadata=metadata or {},
        )

        self._store_metric(metric)

    def get_system_health(self) -> SystemHealth:
        """Get current system health snapshot."""
        # Calculate recent metrics
        recent_metrics = [m for m in self.metrics_history if m.timestamp > datetime.now() - timedelta(minutes=5)]

        if recent_metrics:
            avg_response_time = sum(m.duration_ms for m in recent_metrics) / len(recent_metrics)
            error_rate = sum(1 for m in recent_metrics if not m.success) / len(recent_metrics)
            throughput = len(recent_metrics) / 5.0  # Operations per minute
        else:
            avg_response_time = 0.0
            error_rate = 0.0
            throughput = 0.0

        return SystemHealth(
            timestamp=datetime.now(),
            cpu_usage=self._get_cpu_usage(),
            memory_usage=self._get_memory_usage_percent(),
            disk_usage=self._get_disk_usage(),
            active_threads=threading.active_count(),
            response_time_avg=avg_response_time,
            error_rate=error_rate,
            throughput=throughput,
        )

    def get_component_performance(self, component: str, hours: int = 24) -> dict[str, Any]:
        """Get performance statistics for a specific component.

        Args:
            component: Component name
            hours: Number of hours to analyze

        Returns:
            Dict containing performance statistics

        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        component_metrics = [m for m in self.metrics_history if m.component == component and m.timestamp > cutoff_time]

        if not component_metrics:
            return {
                "component": component,
                "total_operations": 0,
                "success_rate": 0.0,
                "avg_duration_ms": 0.0,
                "min_duration_ms": 0.0,
                "max_duration_ms": 0.0,
                "avg_memory_usage_mb": 0.0,
                "operations_per_hour": 0.0,
            }

        successful_ops = [m for m in component_metrics if m.success]
        durations = [m.duration_ms for m in component_metrics]
        memory_usage = [m.memory_usage_mb for m in component_metrics]

        return {
            "component": component,
            "total_operations": len(component_metrics),
            "success_rate": len(successful_ops) / len(component_metrics),
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "avg_memory_usage_mb": sum(memory_usage) / len(memory_usage),
            "operations_per_hour": len(component_metrics) / hours,
            "error_count": len(component_metrics) - len(successful_ops),
            "p95_duration_ms": self._calculate_percentile(durations, 95),
            "p99_duration_ms": self._calculate_percentile(durations, 99),
        }

    def get_performance_trends(self, hours: int = 24) -> dict[str, Any]:
        """Get performance trends over time.

        Args:
            hours: Number of hours to analyze

        Returns:
            Dict containing trend analysis

        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]

        if not recent_metrics:
            return {"trends": [], "summary": "No data available"}

        # Group metrics by hour
        hourly_metrics = defaultdict(list)
        for metric in recent_metrics:
            hour_key = metric.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_metrics[hour_key].append(metric)

        trends = []
        for hour, metrics in sorted(hourly_metrics.items()):
            avg_duration = sum(m.duration_ms for m in metrics) / len(metrics)
            success_rate = sum(1 for m in metrics if m.success) / len(metrics)

            trends.append(
                {
                    "hour": hour.isoformat(),
                    "operation_count": len(metrics),
                    "avg_duration_ms": avg_duration,
                    "success_rate": success_rate,
                    "throughput": len(metrics),
                }
            )

        return {
            "trends": trends,
            "summary": f"Analyzed {len(recent_metrics)} operations over {hours} hours",
        }

    def get_bottlenecks(self, threshold_ms: float = 1000.0) -> list[dict[str, Any]]:
        """Identify performance bottlenecks.

        Args:
            threshold_ms: Duration threshold for identifying slow operations

        Returns:
            List of bottleneck information

        """
        recent_metrics = [m for m in self.metrics_history if m.timestamp > datetime.now() - timedelta(hours=1)]
        slow_operations = [m for m in recent_metrics if m.duration_ms > threshold_ms]

        # Group by component and operation
        bottlenecks = defaultdict(list)
        for metric in slow_operations:
            key = f"{metric.component}.{metric.operation}"
            bottlenecks[key].append(metric)

        result = []
        for operation, metrics in bottlenecks.items():
            avg_duration = sum(m.duration_ms for m in metrics) / len(metrics)
            result.append(
                {
                    "operation": operation,
                    "occurrence_count": len(metrics),
                    "avg_duration_ms": avg_duration,
                    "max_duration_ms": max(m.duration_ms for m in metrics),
                    "impact_score": len(metrics) * avg_duration,  # Simple impact calculation
                    "recommendations": self._get_optimization_recommendations(operation, avg_duration),
                }
            )

        # Sort by impact score
        result.sort(key=lambda x: x["impact_score"], reverse=True)
        return result

    def _store_metric(self, metric: PerformanceMetric):
        """Store a performance metric."""
        self.metrics_history.append(metric)
        self.component_metrics[metric.component].append(metric)

        # Notify metric callbacks
        self._notify_metric_callbacks(metric)

        # Check for performance alerts
        if self.alerts_enabled:
            self._check_performance_alerts(metric)

    def _check_performance_alerts(self, metric: PerformanceMetric):
        """Check if metric triggers any performance alerts."""
        thresholds = self.performance_thresholds.get(metric.component, {})

        # Duration alert
        if metric.duration_ms > thresholds.get("max_duration_ms", 5000):
            logger.warning("Performance alert: %s.{metric.operation} took {metric.duration_ms}ms", metric.component)

        # Memory alert
        if metric.memory_usage_mb > thresholds.get("max_memory_mb", 100):
            logger.warning("Memory alert: %s.{metric.operation} used {metric.memory_usage_mb}MB", metric.component)

        # Error rate alert
        component_recent = [m for m in self.component_metrics[metric.component][-10:]]
        if len(component_recent) >= 5:
            error_rate = sum(1 for m in component_recent if not m.success) / len(component_recent)
            if error_rate > thresholds.get("max_error_rate", 0.1):
                logger.error("Error rate alert: %s has {error_rate * 100} error rate", metric.component)

    def _background_monitoring(self):
        """Background thread for continuous system monitoring."""
        while self.monitoring_active:
            try:
                # Record system health metrics
                health = self.get_system_health()

                # Check system-level alerts
                if health.cpu_usage > 90:
                    logger.warning("High CPU usage: %.1f%%", health.cpu_usage)

                if health.memory_usage > 90:
                    logger.warning("High memory usage: %.1f%%", health.memory_usage)

                if health.error_rate > 0.1:
                    logger.warning("High error rate: %s", health.error_rate * 100)

                # Sleep for monitoring interval
                time.sleep(30)  # Monitor every 30 seconds

            except (ValueError, TypeError, AttributeError) as e:
                logger.exception("Background monitoring error: %s", e)
                time.sleep(60)  # Wait longer on error

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024

    def _get_memory_usage_percent(self) -> float:
        """Get system memory usage percentage."""
        return psutil.virtual_memory().percent

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        return psutil.cpu_percent(interval=0.1)

    def _get_disk_usage(self) -> float:
        """Get disk usage percentage."""
        return psutil.disk_usage("/").percent

    def _calculate_storage_usage_mb(self) -> float:
        """Calculate the total size of the monitoring storage directory in MB."""
        if not self.config.storage_path:
            return 0.0

        storage_path = Path(self.config.storage_path)
        if not storage_path.is_dir():
            return 0.0

        total_size = 0
        for dirpath, _dirnames, filenames in os.walk(storage_path):
            for f in filenames:
                fp = Path(dirpath) / f
                if fp.is_file():
                    total_size += fp.stat().st_size
        return total_size / (1024 * 1024)  # Convert bytes to MB

    def _calculate_percentile(self, values: list[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int((percentile / 100.0) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]

    def _get_optimization_recommendations(self, operation: str, avg_duration: float) -> list[str]:
        """Get optimization recommendations for slow operations."""
        recommendations = []

        if "pdf_export" in operation:
            recommendations.extend(
                [
                    "Consider reducing PDF complexity or size",
                    "Implement PDF generation caching",
                    "Use background processing for large reports",
                ]
            )
        elif "ai_analysis" in operation:
            recommendations.extend(
                [
                    "Optimize document chunking strategy",
                    "Implement result caching for similar documents",
                    "Consider using smaller AI models for faster processing",
                ]
            )
        elif "database" in operation:
            recommendations.extend(
                [
                    "Add database indexes for frequently queried fields",
                    "Implement query result caching",
                    "Consider database connection pooling",
                ]
            )
        else:
            recommendations.extend(
                [
                    "Profile the operation to identify bottlenecks",
                    "Consider implementing caching",
                    "Optimize algorithm complexity",
                ]
            )

        return recommendations

    def _initialize_thresholds(self) -> dict[str, dict[str, float]]:
        """Initialize performance thresholds for different components."""
        return {
            "pdf_export": {
                "max_duration_ms": 10000,  # 10 seconds
                "max_memory_mb": 200,
                "max_error_rate": 0.05,
            },
            "ai_analysis": {
                "max_duration_ms": 30000,  # 30 seconds
                "max_memory_mb": 500,
                "max_error_rate": 0.1,
            },
            "database": {
                "max_duration_ms": 1000,  # 1 second
                "max_memory_mb": 50,
                "max_error_rate": 0.01,
            },
            "ehr_integration": {
                "max_duration_ms": 15000,  # 15 seconds
                "max_memory_mb": 100,
                "max_error_rate": 0.05,
            },
        }

    def get_status(self) -> MonitoringStatus:
        """Get current monitoring status."""
        if self.state == MonitoringState.STOPPED or self.start_time is None:
            uptime = timedelta()
        else:
            uptime_seconds = time.time() - self._start_time
            uptime = timedelta(seconds=uptime_seconds)

        metrics_count = len(self.metrics_history)
        active_sources = self._get_active_sources_count()

        last_collection = None
        if self.metrics_history:
            last_collection = self.metrics_history[-1].timestamp

        return MonitoringStatus(
            state=self.state,
            uptime=uptime,
            metrics_collected=metrics_count,
            alerts_generated=self._alerts_generated,
            last_collection=last_collection,
            active_sources=active_sources,
            storage_usage_mb=self._calculate_storage_usage_mb(),
            error_count=self._error_count,
            last_error=self._last_error,
        )

    def start_monitoring(self) -> bool:
        """Start the monitoring system."""
        if self.state == MonitoringState.RUNNING:
            return True

        if self.state == MonitoringState.STOPPING:
            return False

        try:
            self.state = MonitoringState.STARTING
            self._initialize_components()

            # Start monitoring thread
            self._monitor_thread = threading.Thread(target=self._background_monitoring, daemon=True)
            self._monitor_thread.start()

            self.state = MonitoringState.RUNNING
            self.start_time = datetime.now()
            self._notify_status_callbacks()
            logger.info("Performance monitoring started")
            return True

        except Exception as e:
            self._last_error = str(e)
            self.state = MonitoringState.ERROR
            self._error_count += 1
            logger.error("Failed to start monitoring: %s", e)
            return False

    def stop_monitoring(self) -> bool:
        """Stop the monitoring system."""
        if self.state == MonitoringState.STOPPED:
            return True

        # If already stopping, don't change state
        if self.state == MonitoringState.STOPPING:
            return True

        try:
            self.state = MonitoringState.STOPPING
            self.monitoring_active = False

            # Wait for thread to finish
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=10.0)

            self._cleanup_components()
            self.state = MonitoringState.STOPPED
            self.start_time = None
            self._notify_status_callbacks()
            logger.info("Performance monitoring stopped")
            return True

        except Exception as e:
            self._last_error = str(e)
            logger.error("Error stopping monitoring: %s", e)
            return True  # Still consider it stopped

    def configure_monitoring(self, config: MonitoringConfiguration) -> bool:
        """Update monitoring configuration."""
        try:
            self.config = config
            self.max_metrics_history = config.max_metrics_history

            # Create storage directory if needed
            if config.storage_path:
                storage_path = Path(config.storage_path)
                storage_path.mkdir(parents=True, exist_ok=True)

            logger.info("Monitoring configuration updated")
            return True

        except Exception as e:
            self._last_error = str(e)
            logger.error("Failed to configure monitoring: %s", e)
            return False

    def add_status_callback(self, callback: Callable) -> None:
        """Add a status change callback."""
        self._status_callbacks.append(callback)

    def remove_status_callback(self, callback: Callable) -> None:
        """Remove a status change callback."""
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)

    def add_metric_callback(self, callback: Callable) -> None:
        """Add a metric collection callback."""
        self._metric_callbacks.append(callback)

    def export_configuration(self, file_path: str) -> bool:
        """Export current configuration to file."""
        try:
            import yaml

            config_dict = {
                "enabled": self.config.enabled,
                "collection_interval": self.config.collection_interval,
                "retention_days": self.config.retention_days,
                "max_metrics_per_batch": self.config.max_metrics_per_batch,
                "max_metrics_history": self.config.max_metrics_history,
                "storage_path": self.config.storage_path,
                "log_level": self.config.log_level,
                "enable_real_time_alerts": self.config.enable_real_time_alerts,
                "enable_predictive_analysis": self.config.enable_predictive_analysis,
                "enable_benchmarking": self.config.enable_benchmarking,
                "cpu_threshold": self.config.cpu_threshold,
                "memory_threshold": self.config.memory_threshold,
                "response_time_threshold": self.config.response_time_threshold,
                "error_rate_threshold": self.config.error_rate_threshold,
                "trend_analysis_window": self.config.trend_analysis_window,
                "anomaly_detection_sensitivity": self.config.anomaly_detection_sensitivity,
                "prediction_horizon": self.config.prediction_horizon,
                "alert_thresholds": self.config.alert_thresholds,
            }

            with open(file_path, "w") as f:
                yaml.dump(config_dict, f)

            logger.info("Configuration exported to %s", file_path)
            return True

        except Exception as e:
            self._last_error = str(e)
            logger.error("Failed to export configuration: %s", e)
            return False

    def import_configuration(self, file_path: str) -> bool:
        """Import configuration from file."""
        try:
            import yaml

            if not Path(file_path).exists():
                raise FileNotFoundError(f"Configuration file not found: {file_path}")

            with open(file_path) as f:
                config_dict = yaml.safe_load(f)

            config = MonitoringConfiguration(**config_dict)
            return self.configure_monitoring(config)

        except Exception as e:
            self._last_error = str(e)
            logger.error("Failed to import configuration: %s", e)
            return False

    def _initialize_components(self) -> None:
        """Initialize monitoring components."""
        try:
            # Initialize metrics collector
            if not self.metrics_collector:
                from src.core.metrics_collector import MetricsCollector

                self.metrics_collector = MetricsCollector(30.0)  # 30 second collection interval

            # Initialize data aggregator
            if not self.data_aggregator:
                from src.core.data_aggregator import DataAggregator

                self.data_aggregator = DataAggregator()

            logger.debug("Monitoring components initialized")

        except Exception as e:
            logger.error("Failed to initialize components: %s", e)
            raise

    def _cleanup_components(self) -> None:
        """Cleanup monitoring components."""
        try:
            if self.metrics_collector and hasattr(self.metrics_collector, "cleanup"):
                self.metrics_collector.cleanup()

            if self.data_aggregator and hasattr(self.data_aggregator, "cleanup"):
                self.data_aggregator.cleanup()

            logger.debug("Monitoring components cleaned up")

        except Exception as e:
            logger.error("Error during component cleanup: %s", e)
        finally:
            # Always clear references even if cleanup fails
            self.metrics_collector = None
            self.data_aggregator = None

    def _get_active_sources_count(self) -> int:
        """Get count of active metric sources."""
        if self.metrics_collector:
            # Try both method names for compatibility
            if hasattr(self.metrics_collector, "get_active_sources_count"):
                count = self.metrics_collector.get_active_sources_count()
                return count if isinstance(count, int) else 0
            elif hasattr(self.metrics_collector, "get_source_count"):
                count = self.metrics_collector.get_source_count()
                return count if isinstance(count, int) else 0
        return 0

    def _notify_status_callbacks(self) -> None:
        """Notify all status callbacks of state change."""
        for callback in self._status_callbacks:
            try:
                callback(self.state)
            except Exception as e:
                logger.error("Error in status callback: %s", e)

    def _notify_status_change(self) -> None:
        """Alias for _notify_status_callbacks for test compatibility."""
        self._notify_status_callbacks()

    def _notify_metric_callbacks(self, metrics) -> None:
        """Notify all metric callbacks of new metrics."""
        # Handle both single metric and list of metrics
        if not isinstance(metrics, list):
            metrics = [metrics]

        for metric in metrics:
            for callback in self._metric_callbacks:
                try:
                    callback(metric)
                except Exception as e:
                    logger.error("Error in metric callback: %s", e)


class OperationTracker:
    """Context manager for tracking individual operations."""

    def __init__(self, monitor, component: str, operation: str, metadata: dict):
        self.monitor = monitor
        self.component = component
        self.operation = operation
        self.metadata = metadata

    def __enter__(self):
        self.start_time = time.time()
        self.start_memory = self.monitor._get_memory_usage()
        self.start_cpu = self.monitor._get_cpu_usage()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        duration_ms = (end_time - self.start_time) * 1000
        end_memory = self.monitor._get_memory_usage()
        end_cpu = self.monitor._get_cpu_usage()

        success = exc_type is None

        metric = PerformanceMetric(
            timestamp=datetime.now(),
            component=self.component,
            operation=self.operation,
            duration_ms=duration_ms,
            memory_usage_mb=end_memory - self.start_memory,
            cpu_usage_percent=(end_cpu + self.start_cpu) / 2,
            success=success,
            metadata=self.metadata,
        )

        self.monitor._store_metric(metric)


# Global performance monitor instance
# Global performance monitor instance
# Global performance monitor instance
performance_monitor = PerformanceMonitor()
