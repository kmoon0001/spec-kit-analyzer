"""Metrics Collector for Performance Monitoring

This module provides comprehensive metric collection from various system
components including system resources, application metrics, and custom sources.
Implements best practices for performance monitoring, error handling, and
resource management.
"""

import asyncio
import logging
import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics that can be collected."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class PerformanceMetric:
    """Individual performance metric with comprehensive metadata."""

    timestamp: datetime
    name: str
    value: float
    unit: str
    metric_type: MetricType
    source: str
    tags: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert metric to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "metric_type": self.metric_type.value,
            "source": self.source,
            "tags": self.tags,
            "metadata": self.metadata,
        }
    
    def __str__(self) -> str:
        """String representation of the metric."""
        return f"{self.name}={self.value}{self.unit} [{self.source}]"


class MetricSource(ABC):
    """Abstract base class for metric sources with enhanced error handling."""

    def __init__(self):
        self._last_collection_time: datetime | None = None
        self._collection_errors: int = 0
        self._max_errors = 5
        self._is_healthy = True

    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of this metric source."""

    @abstractmethod
    async def collect_metrics(self) -> list[PerformanceMetric]:
        """Collect metrics from this source asynchronously."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this metric source is available."""

    def is_healthy(self) -> bool:
        """Check if this metric source is healthy (not too many errors)."""
        return self._is_healthy and self._collection_errors < self._max_errors

    def record_error(self, error: Exception) -> None:
        """Record an error from this metric source."""
        self._collection_errors += 1
        if self._collection_errors >= self._max_errors:
            self._is_healthy = False
            logger.warning(
                "Metric source %s marked as unhealthy after %d errors. Latest: %s",
                self.get_source_name(),
                self._collection_errors,
                error,
            )

    def reset_health(self) -> None:
        """Reset the health status of this metric source."""
        self._collection_errors = 0
        self._is_healthy = True
        logger.info("Reset health status for metric source: %s", self.get_source_name())

    def cleanup(self) -> None:
        """Cleanup resources used by this source. Default implementation does nothing."""
        pass


class SystemMetricsSource(MetricSource):
    """Collects system-level metrics using psutil with comprehensive monitoring."""

    def __init__(self):
        super().__init__()
        self._last_cpu_times: Any | None = None
        self._last_network_io: Any | None = None
        self._last_disk_io: Any | None = None
        self._boot_time: float | None = None
        
    def get_source_name(self) -> str:
        return "system"
    
    def is_available(self) -> bool:
        try:
            import psutil
            return True
        except ImportError:
            logger.warning("psutil not available for system metrics collection")
            return False
    
    async def collect_metrics(self) -> list[PerformanceMetric]:
        """Collect comprehensive system metrics."""
        if not self.is_available():
            return []
        
        metrics = []
        timestamp = datetime.now()
        
        try:
            import psutil
            
            # CPU Metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            metrics.append(PerformanceMetric(
                timestamp=timestamp,
                name="cpu_usage_percent",
                value=cpu_percent,
                unit="%",
                metric_type=MetricType.GAUGE,
                source=self.get_source_name(),
                tags={"component": "cpu"},
                metadata={"cpu_count": psutil.cpu_count()}
            ))
            
            # Memory Metrics
            memory = psutil.virtual_memory()
            metrics.extend([
                PerformanceMetric(
                    timestamp=timestamp,
                    name="memory_usage_percent",
                    value=memory.percent,
                    unit="%",
                    metric_type=MetricType.GAUGE,
                    source=self.get_source_name(),
                    tags={"component": "memory", "type": "virtual"}
                ),
                PerformanceMetric(
                    timestamp=timestamp,
                    name="memory_available_bytes",
                    value=float(memory.available),
                    unit="bytes",
                    metric_type=MetricType.GAUGE,
                    source=self.get_source_name(),
                    tags={"component": "memory", "type": "available"}
                ),
                PerformanceMetric(
                    timestamp=timestamp,
                    name="memory_used_bytes",
                    value=float(memory.used),
                    unit="bytes",
                    metric_type=MetricType.GAUGE,
                    source=self.get_source_name(),
                    tags={"component": "memory", "type": "used"}
                )
            ])
            
            # Disk Metrics
            try:
                disk_usage = psutil.disk_usage('/')
                metrics.extend([
                    PerformanceMetric(
                        timestamp=timestamp,
                        name="disk_usage_percent",
                        value=(disk_usage.used / disk_usage.total) * 100,
                        unit="%",
                        metric_type=MetricType.GAUGE,
                        source=self.get_source_name(),
                        tags={"component": "disk", "mount": "/"}
                    ),
                    PerformanceMetric(
                        timestamp=timestamp,
                        name="disk_free_bytes",
                        value=float(disk_usage.free),
                        unit="bytes",
                        metric_type=MetricType.GAUGE,
                        source=self.get_source_name(),
                        tags={"component": "disk", "mount": "/", "type": "free"}
                    )
                ])
            except (OSError, AttributeError) as e:
                logger.debug("Could not collect disk metrics: %s", e)
            
            # Network Metrics (if available)
            try:
                network_io = psutil.net_io_counters()
                if network_io:
                    metrics.extend([
                        PerformanceMetric(
                            timestamp=timestamp,
                            name="network_bytes_sent",
                            value=float(network_io.bytes_sent),
                            unit="bytes",
                            metric_type=MetricType.COUNTER,
                            source=self.get_source_name(),
                            tags={"component": "network", "direction": "sent"}
                        ),
                        PerformanceMetric(
                            timestamp=timestamp,
                            name="network_bytes_received",
                            value=float(network_io.bytes_recv),
                            unit="bytes",
                            metric_type=MetricType.COUNTER,
                            source=self.get_source_name(),
                            tags={"component": "network", "direction": "received"}
                        )
                    ])
            except (OSError, AttributeError) as e:
                logger.debug("Could not collect network metrics: %s", e)
            
            # Process-specific metrics
            try:
                process = psutil.Process()
                process_memory = process.memory_info()
                metrics.extend([
                    PerformanceMetric(
                        timestamp=timestamp,
                        name="process_memory_rss",
                        value=float(process_memory.rss),
                        unit="bytes",
                        metric_type=MetricType.GAUGE,
                        source=self.get_source_name(),
                        tags={"component": "process", "type": "rss"}
                    ),
                    PerformanceMetric(
                        timestamp=timestamp,
                        name="process_cpu_percent",
                        value=process.cpu_percent(),
                        unit="%",
                        metric_type=MetricType.GAUGE,
                        source=self.get_source_name(),
                        tags={"component": "process", "type": "cpu"}
                    )
                ])
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.debug("Could not collect process metrics: %s", e)
            
            self._last_collection_time = timestamp
            logger.debug("Collected %d system metrics", len(metrics))
            
        except Exception as e:
            self.record_error(e)
            logger.error("Failed to collect system metrics: %s", e)
        
        return metrics



    def _initialize_default_sources(self) -> None:
        """Initialize default metric sources."""
        # System metrics
        system_source = SystemMetricsSource()
        if system_source.is_available():
            self._sources["system"] = system_source

        # Application metrics
        app_source = ApplicationMetricsSource()
        self._sources["application"] = app_source

    def register_source(self, source: MetricSource) -> bool:
        """Register a new metric source.

        Args:
            source: Metric source to register

        Returns:
            True if source was registered successfully

        """
        try:
            source_name = source.get_source_name()

            if not source.is_available():
                logger.warning("Metric source '%s' is not available", source_name)
                return False

            with self._lock:
                if source_name in self._sources:
                    logger.warning("Metric source '%s' already registered", source_name)
                    return False

                self._sources[source_name] = source

            logger.info("Registered metric source: %s", source_name)
            return True

        except Exception as e:
            logger.exception("Failed to register metric source: %s", e)
            return False

    def unregister_source(self, source_name: str) -> bool:
        """Unregister a metric source.

        Args:
            source_name: Name of source to unregister

        Returns:
            True if source was unregistered successfully

        """
        try:
            with self._lock:
                if source_name not in self._sources:
                    logger.warning("Metric source '%s' not found", source_name)
                    return False

                source = self._sources.pop(source_name)
                source.cleanup()

            logger.info("Unregistered metric source: %s", source_name)
            return True

        except Exception:
            logger.exception("Failed to unregister metric source '%s': {e}", source_name)
            return False

    def collect_all_metrics(self) -> list[dict[str, Any]]:
        """Collect all available metrics.

        Returns:
            List of metric dictionaries

        """
        all_metrics = []

        with self._lock:
            sources_to_collect = list(self._sources.items())

        for source_name, source in sources_to_collect:
            try:
                if source.is_available():
                    metrics = source.collect_metrics()

                    # Convert to dictionaries
                    for metric in metrics:
                        metric_dict = {
                            "timestamp": metric.timestamp.isoformat(),
                            "name": metric.name,
                            "value": metric.value,
                            "unit": metric.unit,
                            "type": metric.metric_type.value,
                            "source": metric.source,
                            "tags": metric.tags,
                            "metadata": metric.metadata,
                        }
                        all_metrics.append(metric_dict)

            except (ImportError, ModuleNotFoundError):
                logger.exception("Error collecting metrics from source '%s': {e}", source_name)

        logger.debug("Collected %s metrics from {len(sources_to_collect)} sources", len(all_metrics))
        return all_metrics

    def collect_metrics_from_source(self, source_name: str) -> list[dict[str, Any]]:
        """Collect metrics from a specific source.

        Args:
            source_name: Name of source to collect from

        Returns:
            List of metric dictionaries from the specified source

        """
        with self._lock:
            if source_name not in self._sources:
                logger.warning("Metric source '%s' not found", source_name)
                return []

            source = self._sources[source_name]

        try:
            if not source.is_available():
                logger.warning("Metric source '%s' is not available", source_name)
                return []

            metrics = source.collect_metrics()

            # Convert to dictionaries
            metric_dicts = []
            for metric in metrics:
                metric_dict = {
                    "timestamp": metric.timestamp.isoformat(),
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "type": metric.metric_type.value,
                    "source": metric.source,
                    "tags": metric.tags,
                    "metadata": metric.metadata,
                }
                metric_dicts.append(metric_dict)

            return metric_dicts

        except (ImportError, ModuleNotFoundError):
            logger.exception("Error collecting metrics from source '%s': {e}", source_name)
            return []

    def get_active_sources_count(self) -> int:
        """Get count of active metric sources.

        Returns:
            Number of active metric sources

        """
        with self._lock:
            active_count = 0
            for source in self._sources.values():
                try:
                    if source.is_available():
                        active_count += 1
                except Exception:
                    pass  # Source is not available

            return active_count

    def get_source_names(self) -> list[str]:
        """Get names of all registered sources.

        Returns:
            List of source names

        """
        with self._lock:
            return list(self._sources.keys())

    def get_source_status(self) -> dict[str, bool]:
        """Get availability status of all sources.

        Returns:
            Dictionary mapping source names to availability status

        """
        status = {}

        with self._lock:
            for name, source in self._sources.items():
                try:
                    status[name] = source.is_available()
                except Exception:
                    status[name] = False

        return status

    def get_application_source(self) -> "ApplicationMetricsSource | None":
        """Get the application metrics source for recording metrics.

        Returns:
            Application metrics source if available

        """
        with self._lock:
            source = self._sources.get("application")
            if isinstance(source, ApplicationMetricsSource):
                return source
            return None

    def create_custom_source(self, name: str) -> "CustomMetricsSource":
        """Create and register a custom metrics source.

        Args:
            name: Name for the custom source

        Returns:
            Custom metrics source

        """
        custom_source = CustomMetricsSource(name)
        self.register_source(custom_source)
        return custom_source

    def update_config(self, config) -> None:
        """Update collector configuration.

        Args:
            config: New monitoring configuration

        """
        self.config = config
        logger.debug("Metrics collector configuration updated")



class ApplicationMetricsSource:
    """Application metrics source."""
    
    def __init__(self):
        self.metrics = {}
    
    def get_source_name(self) -> str:
        return "application"
    
    def record_metric(self, name: str, value: float):
        self.metrics[name] = value
    
    def record_response_time(self, endpoint: str, time_ms: float):
        self.metrics[f"response_time_{endpoint}"] = time_ms
    
    def record_request(self, endpoint: str):
        key = f"requests_{endpoint}"
        self.metrics[key] = self.metrics.get(key, 0) + 1
    
    def collect_metrics(self) -> dict:
        return self.get_metrics()

    def get_metrics(self) -> dict:
        return self.metrics.copy()



class CustomMetricsSource:
    """Custom metrics source."""
    
    def __init__(self, name: str):
        self.name = name
        self.metrics = {}
    
    def get_source_name(self) -> str:
        return self.name
    
    def add_metric(self, name: str, value: float):
        """Add a custom metric"""
        self.metrics[name] = value
    
    def record_metric(self, name: str, value: float):
        """Record a custom metric"""
        self.metrics[name] = value
    
    def get_metrics(self) -> dict:
        """Get all recorded metrics"""
        return self.metrics.copy()


class MetricsCollector:
    """Main metrics collection service"""
    
    def __init__(self, config=None):
        self.config = config
        self.sources = []
        self._sources = []
        self.metrics_history = []
    
    def add_source(self, source: MetricSource):
        """Add a metrics source"""
        self.sources.append(source)
        self._sources.append(source)
    
    def collect_metrics(self) -> dict:
        """Collect metrics from all sources"""
        all_metrics = {}
        for source in self.sources:
            try:
                metrics = source.get_metrics()
                all_metrics.update(metrics)
            except Exception as e:
                logger.error(f"Error collecting metrics from {source}: {e}")
        return all_metrics
    
    def get_metrics_history(self) -> list:
        """Get historical metrics"""
        return self.metrics_history.copy()


class ApplicationMetricsSource(MetricSource):
    """Collects application-specific metrics."""

    def __init__(self):
        super().__init__()
        self._response_times: deque = deque(maxlen=1000)
        self._request_counts: defaultdict = defaultdict(int)
        self._error_counts: defaultdict = defaultdict(int)
        self._lock = threading.Lock()

    def get_source_name(self) -> str:
        return "application"

    def is_available(self) -> bool:
        return True

    async def collect_metrics(self) -> list[PerformanceMetric]:
        """Collect application-specific metrics."""
        metrics = []
        timestamp = datetime.now()

        with self._lock:
            # Response time metrics
            if self._response_times:
                response_times = list(self._response_times)
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                min_response_time = min(response_times)

                metrics.extend([
                    PerformanceMetric(
                        timestamp=timestamp,
                        name="response_time_avg",
                        value=avg_response_time,
                        unit="ms",
                        metric_type=MetricType.GAUGE,
                        source=self.get_source_name(),
                        tags={"component": "api", "stat": "average"}
                    ),
                    PerformanceMetric(
                        timestamp=timestamp,
                        name="response_time_max",
                        value=max_response_time,
                        unit="ms",
                        metric_type=MetricType.GAUGE,
                        source=self.get_source_name(),
                        tags={"component": "api", "stat": "maximum"}
                    ),
                    PerformanceMetric(
                        timestamp=timestamp,
                        name="response_time_min",
                        value=min_response_time,
                        unit="ms",
                        metric_type=MetricType.GAUGE,
                        source=self.get_source_name(),
                        tags={"component": "api", "stat": "minimum"}
                    )
                ])

            # Request count metrics
            for endpoint, count in self._request_counts.items():
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    name="request_count",
                    value=float(count),
                    unit="requests",
                    metric_type=MetricType.COUNTER,
                    source=self.get_source_name(),
                    tags={"component": "api", "endpoint": endpoint}
                ))

            # Error count metrics
            for error_type, count in self._error_counts.items():
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    name="error_count",
                    value=float(count),
                    unit="errors",
                    metric_type=MetricType.COUNTER,
                    source=self.get_source_name(),
                    tags={"component": "api", "error_type": error_type}
                ))

        return metrics

    def record_response_time(self, response_time_ms: float) -> None:
        """Record a response time measurement."""
        with self._lock:
            self._response_times.append(response_time_ms)

    def record_request(self, endpoint: str) -> None:
        """Record a request to an endpoint."""
        with self._lock:
            self._request_counts[endpoint] += 1

    def record_error(self, error_type: str) -> None:
        """Record an error occurrence."""
        with self._lock:
            self._error_counts[error_type] += 1

    def reset_counters(self) -> None:
        """Reset all counters (useful for periodic reporting)."""
        with self._lock:
            self._request_counts.clear()
            self._error_counts.clear()


class AIModelMetricsSource(MetricSource):
    """Collects AI model performance metrics."""

    def __init__(self):
        super().__init__()
        self._inference_times: deque = deque(maxlen=500)
        self._model_loads: defaultdict = defaultdict(int)
        self._model_errors: defaultdict = defaultdict(int)
        self._lock = threading.Lock()

    def get_source_name(self) -> str:
        return "ai_models"

    def is_available(self) -> bool:
        return True

    async def collect_metrics(self) -> list[PerformanceMetric]:
        """Collect AI model metrics."""
        metrics = []
        timestamp = datetime.now()

        with self._lock:
            # Inference time metrics
            if self._inference_times:
                inference_times = list(self._inference_times)
                avg_inference_time = sum(inference_times) / len(inference_times)
                
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    name="ai_inference_time_avg",
                    value=avg_inference_time,
                    unit="ms",
                    metric_type=MetricType.GAUGE,
                    source=self.get_source_name(),
                    tags={"component": "ai", "stat": "average"}
                ))

            # Model load counts
            for model_name, count in self._model_loads.items():
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    name="model_load_count",
                    value=float(count),
                    unit="loads",
                    metric_type=MetricType.COUNTER,
                    source=self.get_source_name(),
                    tags={"component": "ai", "model": model_name}
                ))

            # Model error counts
            for model_name, count in self._model_errors.items():
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    name="model_error_count",
                    value=float(count),
                    unit="errors",
                    metric_type=MetricType.COUNTER,
                    source=self.get_source_name(),
                    tags={"component": "ai", "model": model_name}
                ))

        return metrics

    def record_inference_time(self, inference_time_ms: float) -> None:
        """Record an AI inference time."""
        with self._lock:
            self._inference_times.append(inference_time_ms)

    def record_model_load(self, model_name: str) -> None:
        """Record a model load event."""
        with self._lock:
            self._model_loads[model_name] += 1

    def record_model_error(self, model_name: str) -> None:
        """Record a model error."""
        with self._lock:
            self._model_errors[model_name] += 1


class MetricsCollector:
    """Main metrics collector that orchestrates all metric sources."""

    def __init__(self):
        self._sources: dict[str, MetricSource] = {}
        self._collection_interval = 30.0  # seconds
        self._is_running = False
        self._collection_task: asyncio.Task | None = None
        self._metrics_buffer: deque = deque(maxlen=10000)
        self._buffer_lock = threading.Lock()
        self._callbacks: list[Callable[[list[PerformanceMetric]], None]] = []
        
        # Register default sources
        self._register_default_sources()

    def _register_default_sources(self) -> None:
        """Register default metric sources."""
        try:
            system_source = SystemMetricsSource()
            if system_source.is_available():
                self.register_source(system_source)
            
            self.register_source(ApplicationMetricsSource())
            self.register_source(AIModelMetricsSource())
            
            logger.info("Registered %d metric sources", len(self._sources))
        except Exception as e:
            logger.error("Failed to register default metric sources: %s", e)

    def register_source(self, source: MetricSource) -> None:
        """Register a metric source."""
        if not isinstance(source, MetricSource):
            raise ValueError("Source must be an instance of MetricSource")
        
        source_name = source.get_source_name()
        if source_name in self._sources:
            logger.warning("Replacing existing metric source: %s", source_name)
        
        self._sources[source_name] = source
        logger.info("Registered metric source: %s", source_name)

    def unregister_source(self, source_name: str) -> bool:
        """Unregister a metric source."""
        if source_name in self._sources:
            source = self._sources.pop(source_name)
            try:
                source.cleanup()
            except Exception as e:
                logger.warning("Error during cleanup of source %s: %s", source_name, e)
            
            logger.info("Unregistered metric source: %s", source_name)
            return True
        return False

    def add_callback(self, callback: Callable[[list[PerformanceMetric]], None]) -> None:
        """Add a callback to be called when metrics are collected."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[list[PerformanceMetric]], None]) -> None:
        """Remove a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def collect_all_metrics(self) -> list[PerformanceMetric]:
        """Collect metrics from all registered sources."""
        all_metrics = []
        
        for source_name, source in self._sources.items():
            if not source.is_healthy():
                logger.debug("Skipping unhealthy source: %s", source_name)
                continue
            
            try:
                metrics = await source.collect_metrics()
                all_metrics.extend(metrics)
                logger.debug("Collected %d metrics from %s", len(metrics), source_name)
            except Exception as e:
                source.record_error(e)
                logger.error("Failed to collect metrics from %s: %s", source_name, e)
        
        # Store in buffer
        with self._buffer_lock:
            self._metrics_buffer.extend(all_metrics)
        
        # Call callbacks
        for callback in self._callbacks:
            try:
                callback(all_metrics)
            except Exception as e:
                logger.error("Error in metrics callback: %s", e)
        
        return all_metrics

    def get_recent_metrics(self, count: int = 100) -> list[PerformanceMetric]:
        """Get recent metrics from the buffer."""
        with self._buffer_lock:
            return list(self._metrics_buffer)[-count:]

    def get_metrics_by_source(self, source_name: str, count: int = 100) -> list[PerformanceMetric]:
        """Get recent metrics from a specific source."""
        with self._buffer_lock:
            source_metrics = [m for m in self._metrics_buffer if m.source == source_name]
            return source_metrics[-count:]

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get a summary of collected metrics."""
        with self._buffer_lock:
            metrics = list(self._metrics_buffer)
        
        if not metrics:
            return {"total_metrics": 0, "sources": [], "time_range": None}
        
        sources = set(m.source for m in metrics)
        earliest = min(m.timestamp for m in metrics)
        latest = max(m.timestamp for m in metrics)
        
        source_counts = defaultdict(int)
        for metric in metrics:
            source_counts[metric.source] += 1
        
        return {
            "total_metrics": len(metrics),
            "sources": list(sources),
            "source_counts": dict(source_counts),
            "time_range": {
                "earliest": earliest.isoformat(),
                "latest": latest.isoformat(),
                "duration_seconds": (latest - earliest).total_seconds()
            },
            "healthy_sources": [name for name, source in self._sources.items() if source.is_healthy()],
            "unhealthy_sources": [name for name, source in self._sources.items() if not source.is_healthy()]
        }

    async def start_collection(self, interval: float | None = None) -> None:
        """Start automatic metric collection."""
        if self._is_running:
            logger.warning("Metrics collection is already running")
            return
        
        if interval is not None:
            self._collection_interval = interval
        
        self._is_running = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Started metrics collection with interval: %.1fs", self._collection_interval)

    async def stop_collection(self) -> None:
        """Stop automatic metric collection."""
        if not self._is_running:
            return
        
        self._is_running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped metrics collection")

    async def _collection_loop(self) -> None:
        """Main collection loop."""
        while self._is_running:
            try:
                start_time = time.time()
                await self.collect_all_metrics()
                collection_time = (time.time() - start_time) * 1000
                
                logger.debug("Metrics collection took %.2fms", collection_time)
                
                # Wait for the next collection interval
                await asyncio.sleep(self._collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in metrics collection loop: %s", e)
                await asyncio.sleep(min(self._collection_interval, 10.0))

    def cleanup(self) -> None:
        """Cleanup all resources."""
        if self._is_running:
            logger.warning("Stopping metrics collection during cleanup")
        
        for source_name, source in self._sources.items():
            try:
                source.cleanup()
            except Exception as e:
                logger.warning("Error during cleanup of source %s: %s", source_name, e)
        
        self._sources.clear()
        self._callbacks.clear()
        
        with self._buffer_lock:
            self._metrics_buffer.clear()
        
        logger.info("Metrics collector cleanup completed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


# Global metrics collector instance
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def record_response_time(response_time_ms: float) -> None:
    """Convenience function to record response time."""
    collector = get_metrics_collector()
    app_source = collector._sources.get("application")
    if isinstance(app_source, ApplicationMetricsSource):
        app_source.record_response_time(response_time_ms)


def record_request(endpoint: str) -> None:
    """Convenience function to record a request."""
    collector = get_metrics_collector()
    app_source = collector._sources.get("application")
    if isinstance(app_source, ApplicationMetricsSource):
        app_source.record_request(endpoint)


def record_error(error_type: str) -> None:
    """Convenience function to record an error."""
    collector = get_metrics_collector()
    app_source = collector._sources.get("application")
    if isinstance(app_source, ApplicationMetricsSource):
        app_source.record_error(error_type)


def record_ai_inference_time(inference_time_ms: float) -> None:
    """Convenience function to record AI inference time."""
    collector = get_metrics_collector()
    ai_source = collector._sources.get("ai_models")
    if isinstance(ai_source, AIModelMetricsSource):
        ai_source.record_inference_time(inference_time_ms)


def record_model_load(model_name: str) -> None:
    """Convenience function to record model load."""
    collector = get_metrics_collector()
    ai_source = collector._sources.get("ai_models")
    if isinstance(ai_source, AIModelMetricsSource):
        ai_source.record_model_load(model_name)


def record_model_error(model_name: str) -> None:
    """Convenience function to record model error."""
    collector = get_metrics_collector()
    ai_source = collector._sources.get("ai_models")
    if isinstance(ai_source, AIModelMetricsSource):
        ai_source.record_model_error(model_name)