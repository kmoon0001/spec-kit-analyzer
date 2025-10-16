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
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

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

    def __eq__(self, other: object) -> bool:
        """Check equality with another metric."""
        if not isinstance(other, PerformanceMetric):
            return False
        return (
            self.name == other.name
            and self.value == other.value
            and self.source == other.source
            and self.timestamp == other.timestamp
        )


class MetricSource(ABC):
    """Abstract base class for metric sources with enhanced error handling."""

    def __init__(self):
        self._last_collection_time: datetime | None = None
        self._collection_errors: int = 0
        self._max_errors = 5
        self._is_healthy = True
        self._lock = threading.Lock()

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
        with self._lock:
            return self._is_healthy and self._collection_errors < self._max_errors

    def record_error(self, error: Exception) -> None:
        """Record an error from this metric source."""
        with self._lock:
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
        with self._lock:
            self._collection_errors = 0
            self._is_healthy = True
            logger.info("Reset health status for metric source: %s", self.get_source_name())

    def get_last_collection_time(self) -> datetime | None:
        """Get the last collection time."""
        with self._lock:
            return self._last_collection_time

    def cleanup(self) -> None:
        """Cleanup resources used by this source.

        Subclasses can override this method to release resources, but the
        base implementation provides a safe no-op so that lightweight test
        doubles do not need to implement it explicitly.
        """

        return None


class SystemMetricsSource(MetricSource):
    """Collects system-level metrics using psutil with comprehensive monitoring."""

    def __init__(self):
        super().__init__()
        self._last_cpu_times: Any = None
        self._last_network_io: Any = None
        self._last_disk_io: Any = None
        self._boot_time: float | None = None

    def get_source_name(self) -> str:
        return "system"

    def is_available(self) -> bool:
        try:
            __import__("psutil")
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
            metrics.append(
                PerformanceMetric(
                    timestamp=timestamp,
                    name="cpu_usage_percent",
                    value=cpu_percent,
                    unit="%",
                    metric_type=MetricType.GAUGE,
                    source=self.get_source_name(),
                    tags={"component": "cpu"},
                    metadata={"cpu_count": psutil.cpu_count()},
                )
            )

            # Memory Metrics
            memory = psutil.virtual_memory()
            metrics.extend(
                [
                    PerformanceMetric(
                        timestamp=timestamp,
                        name="memory_usage_percent",
                        value=memory.percent,
                        unit="%",
                        metric_type=MetricType.GAUGE,
                        source=self.get_source_name(),
                        tags={"component": "memory", "type": "virtual"},
                    ),
                    PerformanceMetric(
                        timestamp=timestamp,
                        name="memory_available_bytes",
                        value=float(memory.available),
                        unit="bytes",
                        metric_type=MetricType.GAUGE,
                        source=self.get_source_name(),
                        tags={"component": "memory", "type": "available"},
                    ),
                ]
            )

            # Disk Metrics
            try:
                disk_usage = psutil.disk_usage("/")
                metrics.append(
                    PerformanceMetric(
                        timestamp=timestamp,
                        name="disk_usage_percent",
                        value=(disk_usage.used / disk_usage.total) * 100,
                        unit="%",
                        metric_type=MetricType.GAUGE,
                        source=self.get_source_name(),
                        tags={"component": "disk", "mount": "/"},
                    )
                )
            except (OSError, AttributeError) as e:
                logger.debug("Could not collect disk metrics: %s", e)

            # Process-specific metrics
            try:
                process = psutil.Process()
                process_memory = process.memory_info()
                metrics.extend(
                    [
                        PerformanceMetric(
                            timestamp=timestamp,
                            name="process_memory_rss",
                            value=float(process_memory.rss),
                            unit="bytes",
                            metric_type=MetricType.GAUGE,
                            source=self.get_source_name(),
                            tags={"component": "process", "type": "rss"},
                        ),
                        PerformanceMetric(
                            timestamp=timestamp,
                            name="process_cpu_percent",
                            value=process.cpu_percent(),
                            unit="%",
                            metric_type=MetricType.GAUGE,
                            source=self.get_source_name(),
                            tags={"component": "process", "type": "cpu"},
                        ),
                    ]
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.debug("Could not collect process metrics: %s", e)

            with self._lock:
                self._last_collection_time = timestamp
            logger.debug("Collected %d system metrics", len(metrics))

        except Exception as e:
            self.record_error(e)
            logger.error("Failed to collect system metrics: %s", e)

        return metrics


class ApplicationMetricsSource(MetricSource):
    """Collects application-specific metrics with thread-safe operations."""

    def __init__(self):
        super().__init__()
        self._response_times: deque = deque(maxlen=1000)
        self._request_counts: defaultdict = defaultdict(int)
        self._error_counts: defaultdict = defaultdict(int)
        self._metrics_lock = threading.Lock()

    def get_source_name(self) -> str:
        return "application"

    def is_available(self) -> bool:
        return True

    async def collect_metrics(self) -> list[PerformanceMetric]:
        """Collect application-specific metrics."""
        metrics = []
        timestamp = datetime.now()

        with self._metrics_lock:
            # Response time metrics
            if self._response_times:
                response_times = list(self._response_times)
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                min_response_time = min(response_times)

                metrics.extend(
                    [
                        PerformanceMetric(
                            timestamp=timestamp,
                            name="response_time_avg",
                            value=avg_response_time,
                            unit="ms",
                            metric_type=MetricType.GAUGE,
                            source=self.get_source_name(),
                            tags={"component": "api", "stat": "average"},
                        ),
                        PerformanceMetric(
                            timestamp=timestamp,
                            name="response_time_max",
                            value=max_response_time,
                            unit="ms",
                            metric_type=MetricType.GAUGE,
                            source=self.get_source_name(),
                            tags={"component": "api", "stat": "maximum"},
                        ),
                        PerformanceMetric(
                            timestamp=timestamp,
                            name="response_time_min",
                            value=min_response_time,
                            unit="ms",
                            metric_type=MetricType.GAUGE,
                            source=self.get_source_name(),
                            tags={"component": "api", "stat": "minimum"},
                        ),
                    ]
                )

            # Request count metrics
            for endpoint, count in self._request_counts.items():
                metrics.append(
                    PerformanceMetric(
                        timestamp=timestamp,
                        name="request_count",
                        value=float(count),
                        unit="requests",
                        metric_type=MetricType.COUNTER,
                        source=self.get_source_name(),
                        tags={"component": "api", "endpoint": endpoint},
                    )
                )
            # Error count metrics
            for error_type, count in self._error_counts.items():
                metrics.append(
                    PerformanceMetric(
                        timestamp=timestamp,
                        name="error_count",
                        value=float(count),
                        unit="errors",
                        metric_type=MetricType.COUNTER,
                        source=self.get_source_name(),
                        tags={"component": "api", "error_type": error_type},
                    )
                )

        with self._lock:
            self._last_collection_time = timestamp

        return metrics

    def record_response_time(self, response_time_ms: float) -> None:
        """Record a response time measurement."""
        if response_time_ms < 0:
            logger.warning("Invalid response time: %f", response_time_ms)
            return

        with self._metrics_lock:
            self._response_times.append(response_time_ms)

    def record_request(self, endpoint: str) -> None:
        """Record a request to an endpoint."""
        if not endpoint or not endpoint.strip():
            logger.warning("Invalid endpoint for request recording")
            return

        with self._metrics_lock:
            self._request_counts[endpoint.strip()] += 1

    def record_error(self, error: Exception) -> None:
        """Record an error occurrence."""
        error_type = type(error).__name__
        with self._metrics_lock:
            self._error_counts[error_type] += 1
    
    def record_error_by_type(self, error_type: str) -> None:
        """Record an error occurrence by type string."""
        if not error_type or not error_type.strip():
            logger.warning("Invalid error type for error recording")
            return

        with self._metrics_lock:
            self._error_counts[error_type.strip()] += 1

    def reset_counters(self) -> None:
        """Reset all counters (useful for periodic reporting)."""
        with self._metrics_lock:
            self._request_counts.clear()
            self._error_counts.clear()
            logger.debug("Reset application metrics counters")

    def get_current_stats(self) -> dict[str, Any]:
        """Get current statistics snapshot."""
        with self._metrics_lock:
            response_times = list(self._response_times)
            return {
                "response_times_count": len(response_times),
                "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
                "total_requests": sum(self._request_counts.values()),
                "total_errors": sum(self._error_counts.values()),
                "unique_endpoints": len(self._request_counts),
                "unique_error_types": len(self._error_counts),
            }


class AIModelMetricsSource(MetricSource):
    """Collects AI model performance metrics with enhanced tracking."""

    def __init__(self):
        super().__init__()
        self._inference_times: deque = deque(maxlen=500)
        self._model_loads: defaultdict = defaultdict(int)
        self._model_errors: defaultdict = defaultdict(int)
        self._model_cache_hits: defaultdict = defaultdict(int)
        self._model_cache_misses: defaultdict = defaultdict(int)
        self._metrics_lock = threading.Lock()

    def get_source_name(self) -> str:
        return "ai_models"

    def is_available(self) -> bool:
        return True

    async def collect_metrics(self) -> list[PerformanceMetric]:
        """Collect AI model metrics."""
        metrics = []
        timestamp = datetime.now()

        with self._metrics_lock:
            # Inference time metrics
            if self._inference_times:
                inference_times = list(self._inference_times)
                avg_inference_time = sum(inference_times) / len(inference_times)

                metrics.extend(
                    [
                        PerformanceMetric(
                            timestamp=timestamp,
                            name="ai_inference_time_avg",
                            value=avg_inference_time,
                            unit="ms",
                            metric_type=MetricType.GAUGE,
                            source=self.get_source_name(),
                            tags={"component": "ai", "stat": "average"},
                        ),
                        PerformanceMetric(
                            timestamp=timestamp,
                            name="ai_inference_count",
                            value=float(len(inference_times)),
                            unit="count",
                            metric_type=MetricType.GAUGE,
                            source=self.get_source_name(),
                            tags={"component": "ai", "stat": "total"},
                        ),
                    ]
                )

            # Model load counts
            for model_name, count in self._model_loads.items():
                metrics.append(
                    PerformanceMetric(
                        timestamp=timestamp,
                        name="model_load_count",
                        value=float(count),
                        unit="loads",
                        metric_type=MetricType.COUNTER,
                        source=self.get_source_name(),
                        tags={"component": "ai", "model": model_name},
                    )
                )

            # Model error counts
            for model_name, count in self._model_errors.items():
                metrics.append(
                    PerformanceMetric(
                        timestamp=timestamp,
                        name="model_error_count",
                        value=float(count),
                        unit="errors",
                        metric_type=MetricType.COUNTER,
                        source=self.get_source_name(),
                        tags={"component": "ai", "model": model_name},
                    )
                )
            # Cache performance metrics
            for model_name in set(self._model_cache_hits.keys()) | set(self._model_cache_misses.keys()):
                hits = self._model_cache_hits[model_name]
                misses = self._model_cache_misses[model_name]
                total = hits + misses
                hit_rate = (hits / total * 100) if total > 0 else 0

                metrics.append(
                    PerformanceMetric(
                        timestamp=timestamp,
                        name="model_cache_hit_rate",
                        value=hit_rate,
                        unit="%",
                        metric_type=MetricType.GAUGE,
                        source=self.get_source_name(),
                        tags={"component": "ai", "model": model_name, "stat": "cache_performance"},
                    )
                )

        with self._lock:
            self._last_collection_time = timestamp

        return metrics

    def record_inference_time(self, inference_time_ms: float) -> None:
        """Record an AI inference time."""
        if inference_time_ms < 0:
            logger.warning("Invalid inference time: %f", inference_time_ms)
            return

        with self._metrics_lock:
            self._inference_times.append(inference_time_ms)

    def record_model_load(self, model_name: str) -> None:
        """Record a model load event."""
        if not model_name or not model_name.strip():
            logger.warning("Invalid model name for load recording")
            return

        with self._metrics_lock:
            self._model_loads[model_name.strip()] += 1

    def record_model_error(self, model_name: str) -> None:
        """Record a model error."""
        if not model_name or not model_name.strip():
            logger.warning("Invalid model name for error recording")
            return

        with self._metrics_lock:
            self._model_errors[model_name.strip()] += 1

    def record_cache_hit(self, model_name: str) -> None:
        """Record a cache hit for a model."""
        if not model_name or not model_name.strip():
            logger.warning("Invalid model name for cache hit recording")
            return

        with self._metrics_lock:
            self._model_cache_hits[model_name.strip()] += 1

    def record_cache_miss(self, model_name: str) -> None:
        """Record a cache miss for a model."""
        if not model_name or not model_name.strip():
            logger.warning("Invalid model name for cache miss recording")
            return

        with self._metrics_lock:
            self._model_cache_misses[model_name.strip()] += 1


class MetricsCollector:
    """Main metrics collector that orchestrates all metric sources with enhanced capabilities."""

    def __init__(self, collection_interval: float = 30.0):
        self._sources: dict[str, MetricSource] = {}
        self._collection_interval = max(1.0, collection_interval)  # Minimum 1 second
        self._is_running = False
        self._collection_task: asyncio.Task | None = None
        self._metrics_buffer: deque = deque(maxlen=10000)
        self._buffer_lock = threading.Lock()
        self._callbacks: list[Callable[[list[PerformanceMetric]], None]] = []
        self._stats: dict[str, int | float | datetime | None] = {
            "total_collections": 0,
            "failed_collections": 0,
            "last_collection_time": None,
            "collection_duration_ms": 0.0,
        }
        self._stats_lock = threading.Lock()

        # Register default sources
        self._register_default_sources()

    def _register_default_sources(self) -> None:
        """Register default metric sources."""
        try:
            # System metrics (if available)
            system_source = SystemMetricsSource()
            if system_source.is_available():
                self.register_source(system_source)

            # Application metrics (always available)
            self.register_source(ApplicationMetricsSource())

            # AI model metrics (always available)
            self.register_source(AIModelMetricsSource())

            logger.info("Registered %d default metric sources", len(self._sources))
        except Exception as e:
            logger.error("Failed to register default metric sources: %s", e)

    def register_source(self, source: MetricSource) -> None:
        """Register a metric source with validation."""
        if not isinstance(source, MetricSource):
            raise ValueError("Source must be an instance of MetricSource")

        if not source.is_available():
            logger.warning("Registering unavailable source: %s", source.get_source_name())

        source_name = source.get_source_name()
        if not source_name or not source_name.strip():
            raise ValueError("Source name cannot be empty")

        if source_name in self._sources:
            logger.warning("Replacing existing metric source: %s", source_name)

        self._sources[source_name] = source
        logger.info("Registered metric source: %s", source_name)

    def unregister_source(self, source_name: str) -> bool:
        """Unregister a metric source."""
        if not source_name or source_name not in self._sources:
            logger.warning("Source not found for unregistration: %s", source_name)
            return False

        try:
            source = self._sources.pop(source_name)
            source.cleanup()
            logger.info("Unregistered metric source: %s", source_name)
            return True
        except Exception as e:
            logger.error("Failed to unregister source %s: %s", source_name, e)
            return False

    async def collect_all_metrics(self) -> list[PerformanceMetric]:
        """Collect metrics from all available sources."""
        all_metrics = []
        start_time = time.time()

        with self._stats_lock:
            current_count = self._stats["total_collections"]
            if isinstance(current_count, (int, float)):
                self._stats["total_collections"] = current_count + 1
            else:
                self._stats["total_collections"] = 1

        # Collect from all sources concurrently
        tasks = []
        for source_name, source in self._sources.items():
            if source.is_available() and source.is_healthy():
                task = asyncio.create_task(self._collect_from_source_safely(source_name, source))
                tasks.append(task)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, list):
                    all_metrics.extend(result)
                elif isinstance(result, Exception):
                    logger.error("Error in concurrent metric collection: %s", result)
                    with self._stats_lock:
                        current_count = self._stats["failed_collections"]
                        if isinstance(current_count, (int, float)):
                            self._stats["failed_collections"] = current_count + 1
                        else:
                            self._stats["failed_collections"] = 1

        # Update collection stats
        collection_duration = (time.time() - start_time) * 1000  # Convert to ms
        with self._stats_lock:
            self._stats["last_collection_time"] = datetime.now()
            self._stats["collection_duration_ms"] = collection_duration

        # Store in buffer
        with self._buffer_lock:
            self._metrics_buffer.extend(all_metrics)

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(all_metrics)
            except Exception as e:
                logger.error("Error in metrics callback: %s", e)

        logger.debug(
            "Collected %d metrics from %d sources in %.2fms", len(all_metrics), len(tasks), collection_duration
        )

        return all_metrics

    async def _collect_from_source_safely(self, source_name: str, source: MetricSource) -> list[PerformanceMetric]:
        """Safely collect metrics from a single source with error handling."""
        try:
            metrics = await source.collect_metrics()
            if not isinstance(metrics, list):
                logger.warning("Source %s returned non-list metrics", source_name)
                return []
            return metrics
        except Exception as e:
            source.record_error(e)
            logger.error("Failed to collect metrics from source %s: %s", source_name, e)
            return []

    def start_collection(self) -> None:
        """Start automatic metric collection."""
        if self._is_running:
            logger.warning("Metrics collection is already running")
            return

        self._is_running = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Started metrics collection with interval %.1fs", self._collection_interval)

    def stop_collection(self) -> None:
        """Stop automatic metric collection."""
        if not self._is_running:
            logger.warning("Metrics collection is not running")
            return

        self._is_running = False
        if self._collection_task:
            self._collection_task.cancel()
            self._collection_task = None

        logger.info("Stopped metrics collection")

    async def _collection_loop(self) -> None:
        """Main collection loop that runs in the background."""
        logger.info("Starting metrics collection loop")

        while self._is_running:
            try:
                await self.collect_all_metrics()
                await asyncio.sleep(self._collection_interval)
            except asyncio.CancelledError:
                logger.info("Metrics collection loop cancelled")
                break
            except Exception as e:
                logger.error("Error in metrics collection loop: %s", e)
                await asyncio.sleep(min(self._collection_interval, 10.0))  # Backoff on error

    def add_callback(self, callback: Callable[[list[PerformanceMetric]], None]) -> None:
        """Add a callback to be called when metrics are collected."""
        if not callable(callback):
            raise ValueError("Callback must be callable")

        self._callbacks.append(callback)
        logger.debug("Added metrics callback")

    def remove_callback(self, callback: Callable[[list[PerformanceMetric]], None]) -> bool:
        """Remove a callback."""
        try:
            self._callbacks.remove(callback)
            logger.debug("Removed metrics callback")
            return True
        except ValueError:
            logger.warning("Callback not found for removal")
            return False

    def get_recent_metrics(self, count: int = 100) -> list[PerformanceMetric]:
        """Get recent metrics from the buffer."""
        count = max(1, min(count, len(self._metrics_buffer)))

        with self._buffer_lock:
            # Return the most recent metrics
            return list(self._metrics_buffer)[-count:]

    def get_metrics_by_source(self, source_name: str, count: int = 100) -> list[PerformanceMetric]:
        """Get recent metrics from a specific source."""
        with self._buffer_lock:
            source_metrics = [m for m in self._metrics_buffer if m.source == source_name]
            return source_metrics[-count:] if source_metrics else []

    def get_source_status(self) -> dict[str, dict[str, Any]]:
        """Get status information for all sources."""
        status = {}

        for source_name, source in self._sources.items():
            status[source_name] = {
                "available": source.is_available(),
                "healthy": source.is_healthy(),
                "last_collection": source.get_last_collection_time(),
                "error_count": source._collection_errors,
            }

        return status

    def get_collector_stats(self) -> dict[str, Any]:
        """Get collector statistics."""
        with self._stats_lock:
            stats = self._stats.copy()

        with self._buffer_lock:
            stats["buffer_size"] = len(self._metrics_buffer)
            stats["buffer_max_size"] = self._metrics_buffer.maxlen

        stats.update(
            {
                "is_running": self._is_running,
                "collection_interval": self._collection_interval,
                "registered_sources": len(self._sources),
                "active_callbacks": len(self._callbacks),
            }
        )

        return stats

    def reset_source_health(self, source_name: str) -> bool:
        """Reset health status for a specific source."""
        if source_name not in self._sources:
            logger.warning("Source not found for health reset: %s", source_name)
            return False

        self._sources[source_name].reset_health()
        return True

    def cleanup(self) -> None:
        """Cleanup all resources."""
        logger.info("Cleaning up metrics collector")

        # Stop collection
        self.stop_collection()

        # Cleanup all sources
        for source_name, source in self._sources.items():
            try:
                source.cleanup()
            except Exception as e:
                logger.error("Error cleaning up source %s: %s", source_name, e)

        # Clear data structures
        self._sources.clear()
        self._callbacks.clear()

        with self._buffer_lock:
            self._metrics_buffer.clear()


# Global metrics collector instance
_metrics_collector: MetricsCollector | None = None
_collector_lock = threading.Lock()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance (thread-safe singleton)."""
    global _metrics_collector

    if _metrics_collector is None:
        with _collector_lock:
            if _metrics_collector is None:  # Double-check locking
                _metrics_collector = MetricsCollector()

    return _metrics_collector


def reset_metrics_collector() -> None:
    """Reset the global metrics collector (useful for testing)."""
    global _metrics_collector

    with _collector_lock:
        if _metrics_collector is not None:
            _metrics_collector.cleanup()
            _metrics_collector = None


# Convenience functions for common metric recording
def record_response_time(response_time_ms: float) -> None:
    """Convenience function to record response time."""
    try:
        collector = get_metrics_collector()
        app_source = collector._sources.get("application")
        if isinstance(app_source, ApplicationMetricsSource):
            app_source.record_response_time(response_time_ms)
    except Exception as e:
        logger.error("Failed to record response time: %s", e)


def record_request(endpoint: str) -> None:
    """Convenience function to record a request."""
    try:
        collector = get_metrics_collector()
        app_source = collector._sources.get("application")
        if isinstance(app_source, ApplicationMetricsSource):
            app_source.record_request(endpoint)
    except Exception as e:
        logger.error("Failed to record request: %s", e)


def record_error(error_type: str) -> None:
    """Convenience function to record an error."""
    try:
        collector = get_metrics_collector()
        app_source = collector._sources.get("application")
        if isinstance(app_source, ApplicationMetricsSource):
            app_source.record_error_by_type(error_type)
    except Exception as e:
        logger.error("Failed to record error: %s", e)


def record_ai_inference_time(inference_time_ms: float) -> None:
    """Convenience function to record AI inference time."""
    try:
        collector = get_metrics_collector()
        ai_source = collector._sources.get("ai_models")
        if isinstance(ai_source, AIModelMetricsSource):
            ai_source.record_inference_time(inference_time_ms)
    except Exception as e:
        logger.error("Failed to record AI inference time: %s", e)


def record_model_load(model_name: str) -> None:
    """Convenience function to record model load."""
    try:
        collector = get_metrics_collector()
        ai_source = collector._sources.get("ai_models")
        if isinstance(ai_source, AIModelMetricsSource):
            ai_source.record_model_load(model_name)
    except Exception as e:
        logger.error("Failed to record model load: %s", e)


def record_model_error(model_name: str) -> None:
    """Convenience function to record model error."""
    try:
        collector = get_metrics_collector()
        ai_source = collector._sources.get("ai_models")
        if isinstance(ai_source, AIModelMetricsSource):
            ai_source.record_model_error(model_name)
    except Exception as e:
        logger.error("Failed to record model error: %s", e)


def record_cache_hit(model_name: str) -> None:
    """Convenience function to record cache hit."""
    try:
        collector = get_metrics_collector()
        ai_source = collector._sources.get("ai_models")
        if isinstance(ai_source, AIModelMetricsSource):
            ai_source.record_cache_hit(model_name)
    except Exception as e:
        logger.error("Failed to record cache hit: %s", e)


def record_cache_miss(model_name: str) -> None:
    """Convenience function to record cache miss."""
    try:
        collector = get_metrics_collector()
        ai_source = collector._sources.get("ai_models")
        if isinstance(ai_source, AIModelMetricsSource):
            ai_source.record_cache_miss(model_name)
    except Exception as e:
        logger.error("Failed to record cache miss: %s", e)
