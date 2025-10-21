"""Performance metrics collection system.

Provides comprehensive performance monitoring including:
- Request/response timing
- Memory usage tracking
- Database query performance
- AI model inference timing
- System resource monitoring
- Custom business metrics
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """A single metric data point."""

    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""

    request_count: int = 0
    request_duration_ms: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    database_query_count: int = 0
    database_query_duration_ms: float = 0.0
    ai_inference_count: int = 0
    ai_inference_duration_ms: float = 0.0
    error_count: int = 0
    cache_hit_rate: float = 0.0


class MetricsCollector:
    """Collects and aggregates performance metrics."""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.current_metrics = PerformanceMetrics()
        self.lock = Lock()
        self.start_time = time.time()

        # Custom metrics storage
        self.custom_metrics: Dict[str, List[MetricPoint]] = defaultdict(list)

        # Performance thresholds
        self.thresholds = {
            "slow_request_ms": 5000,  # 5 seconds
            "high_memory_mb": 2000,  # 2GB (increased for AI models)
            "high_cpu_percent": 80,  # 80%
            "slow_db_query_ms": 1000,  # 1 second
            "slow_ai_inference_ms": 10000,  # 10 seconds
        }

    def record_request(self, duration_ms: float, status_code: int, endpoint: str):
        """Record a request metric."""
        with self.lock:
            self.current_metrics.request_count += 1
            self.current_metrics.request_duration_ms += duration_ms

            if status_code >= 400:
                self.current_metrics.error_count += 1

            # Check for slow requests
            if duration_ms > self.thresholds["slow_request_ms"]:
                logger.warning(
                    f"Slow request detected: {endpoint} took {duration_ms:.2f}ms"
                )

            # Add to history
            self._add_to_history(
                "request",
                duration_ms,
                {"endpoint": endpoint, "status": str(status_code)},
            )

    def record_database_query(self, duration_ms: float, query_type: str = "unknown"):
        """Record a database query metric."""
        with self.lock:
            self.current_metrics.database_query_count += 1
            self.current_metrics.database_query_duration_ms += duration_ms

            # Check for slow queries
            if duration_ms > self.thresholds["slow_db_query_ms"]:
                logger.warning(
                    f"Slow database query detected: {query_type} took {duration_ms:.2f}ms"
                )

            # Add to history
            self._add_to_history("db_query", duration_ms, {"query_type": query_type})

    def record_ai_inference(self, duration_ms: float, model_type: str = "unknown"):
        """Record an AI inference metric."""
        with self.lock:
            self.current_metrics.ai_inference_count += 1
            self.current_metrics.ai_inference_duration_ms += duration_ms

            # Check for slow inference
            if duration_ms > self.thresholds["slow_ai_inference_ms"]:
                logger.warning(
                    f"Slow AI inference detected: {model_type} took {duration_ms:.2f}ms"
                )

            # Add to history
            self._add_to_history(
                "ai_inference", duration_ms, {"model_type": model_type}
            )

    def record_cache_operation(self, hit: bool, cache_type: str = "unknown"):
        """Record a cache operation."""
        with self.lock:
            # Calculate hit rate
            total_ops = self.current_metrics.request_count
            if total_ops > 0:
                hits = int(self.current_metrics.cache_hit_rate * total_ops / 100)
                if hit:
                    hits += 1
                self.current_metrics.cache_hit_rate = (hits / total_ops) * 100

            # Add to history
            self._add_to_history("cache", 1 if hit else 0, {"cache_type": cache_type})

    def record_custom_metric(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ):
        """Record a custom metric."""
        with self.lock:
            metric_point = MetricPoint(
                timestamp=datetime.now(timezone.utc), value=value, tags=tags or {}
            )
            self.custom_metrics[name].append(metric_point)

            # Keep only recent metrics
            if len(self.custom_metrics[name]) > self.max_history:
                self.custom_metrics[name] = self.custom_metrics[name][
                    -self.max_history :
                ]

    def update_system_metrics(self):
        """Update system resource metrics."""
        try:
            # Memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)

            with self.lock:
                self.current_metrics.memory_usage_mb = memory_mb
                self.current_metrics.cpu_usage_percent = cpu_percent

                # Check thresholds
                if memory_mb > self.thresholds["high_memory_mb"]:
                    logger.warning(f"High memory usage detected: {memory_mb:.2f}MB")

                if cpu_percent > self.thresholds["high_cpu_percent"]:
                    logger.warning(f"High CPU usage detected: {cpu_percent:.2f}%")

                # Add to history
                self._add_to_history("memory", memory_mb)
                self._add_to_history("cpu", cpu_percent)

        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")

    def _add_to_history(
        self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
    ):
        """Add a metric point to history."""
        metric_point = MetricPoint(
            timestamp=datetime.now(timezone.utc), value=value, tags=tags or {}
        )
        self.metrics_history.append((metric_name, metric_point))

    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current metrics snapshot."""
        with self.lock:
            return PerformanceMetrics(
                request_count=self.current_metrics.request_count,
                request_duration_ms=self.current_metrics.request_duration_ms,
                memory_usage_mb=self.current_metrics.memory_usage_mb,
                cpu_usage_percent=self.current_metrics.cpu_usage_percent,
                database_query_count=self.current_metrics.database_query_count,
                database_query_duration_ms=self.current_metrics.database_query_duration_ms,
                ai_inference_count=self.current_metrics.ai_inference_count,
                ai_inference_duration_ms=self.current_metrics.ai_inference_duration_ms,
                error_count=self.current_metrics.error_count,
                cache_hit_rate=self.current_metrics.cache_hit_rate,
            )

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a comprehensive metrics summary."""
        current = self.get_current_metrics()
        uptime = time.time() - self.start_time

        # Calculate averages
        avg_request_duration = (
            current.request_duration_ms / current.request_count
            if current.request_count > 0
            else 0
        )

        avg_db_query_duration = (
            current.database_query_duration_ms / current.database_query_count
            if current.database_query_count > 0
            else 0
        )

        avg_ai_inference_duration = (
            current.ai_inference_duration_ms / current.ai_inference_count
            if current.ai_inference_count > 0
            else 0
        )

        error_rate = (
            (current.error_count / current.request_count) * 100
            if current.request_count > 0
            else 0
        )

        return {
            "uptime_seconds": round(uptime, 2),
            "requests": {
                "total": current.request_count,
                "avg_duration_ms": round(avg_request_duration, 2),
                "error_count": current.error_count,
                "error_rate_percent": round(error_rate, 2),
            },
            "database": {
                "query_count": current.database_query_count,
                "avg_duration_ms": round(avg_db_query_duration, 2),
            },
            "ai_inference": {
                "count": current.ai_inference_count,
                "avg_duration_ms": round(avg_ai_inference_duration, 2),
            },
            "system": {
                "memory_usage_mb": round(current.memory_usage_mb, 2),
                "cpu_usage_percent": round(current.cpu_usage_percent, 2),
            },
            "cache": {"hit_rate_percent": round(current.cache_hit_rate, 2)},
            "custom_metrics": {
                name: len(metrics) for name, metrics in self.custom_metrics.items()
            },
        }

    def reset_metrics(self):
        """Reset all metrics."""
        with self.lock:
            self.current_metrics = PerformanceMetrics()
            self.metrics_history.clear()
            self.custom_metrics.clear()
            self.start_time = time.time()
            logger.info("Metrics reset")


# Global metrics collector
metrics_collector = MetricsCollector()


# Context managers for easy metric collection
class RequestTimer:
    """Context manager for timing requests."""

    def __init__(self, endpoint: str, status_code: int = 200):
        self.endpoint = endpoint
        self.status_code = status_code
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            metrics_collector.record_request(
                duration_ms, self.status_code, self.endpoint
            )


class DatabaseQueryTimer:
    """Context manager for timing database queries."""

    def __init__(self, query_type: str = "unknown"):
        self.query_type = query_type
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            metrics_collector.record_database_query(duration_ms, self.query_type)


class AIInferenceTimer:
    """Context manager for timing AI inference."""

    def __init__(self, model_type: str = "unknown"):
        self.model_type = model_type
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            metrics_collector.record_ai_inference(duration_ms, self.model_type)


# Background task for updating system metrics
async def update_system_metrics_task():
    """Background task to update system metrics periodically."""
    while True:
        try:
            metrics_collector.update_system_metrics()
            await asyncio.sleep(10)  # Update every 10 seconds
        except Exception as e:
            logger.error(f"System metrics update failed: {e}")
            await asyncio.sleep(30)  # Wait longer on error
