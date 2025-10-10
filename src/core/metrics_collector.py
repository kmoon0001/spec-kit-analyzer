"""Metrics Collector for Performance Monitoring

This module provides comprehensive metric collection from various system
components including system resources, application metrics, and custom sources.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
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
    """Individual performance metric."""

    timestamp: datetime
    name: str
    value: float
    unit: str
    metric_type: MetricType
    source: str
    tags: dict[str, str]
    metadata: dict[str, Any]


class MetricSource(ABC):
    """Abstract base class for metric sources."""

    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of this metric source."""

    @abstractmethod
    def collect_metrics(self) -> list[PerformanceMetric]:
        """Collect metrics from this source."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this metric source is available."""

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources used by this source."""


class SystemMetricsSource(MetricSource):
    """Collects system-level metrics using psutil."""

    def __init__(self):
        self._last_cpu_times: Any | None = None
        self._last_network_io: Any | None = None
        self._last_disk_io: Any | None = None
        self._collection_time: datetime | None = None

    def record_response_time(self, response_time_ms: float) -> None:
        """Record a response time measurement."""
        with self._lock:
            self._response_times.append(response_time_ms)

    def record_request(self, endpoint: str) -> None:
        """Record a request to an endpoint."""
        with self._lock:
            self._request_counts[endpoint] = self._request_counts.get(endpoint, 0) + 1

    def record_error(self, endpoint: str, error_type: str) -> None:
        """Record an error for an endpoint."""
        with self._lock:
            key = f"{endpoint}:{error_type}"
            self._error_counts[key] = self._error_counts.get(key, 0) + 1

    def add_metric(self, metric: PerformanceMetric) -> None:
        """Add a custom metric."""
        with self._lock:
            self._metrics.append(metric)

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

    def get_application_source(self) -> ApplicationMetricsSource | None:
        """Get the application metrics source for recording metrics.

        Returns:
            Application metrics source if available

        """
        with self._lock:
            source = self._sources.get("application")
            if isinstance(source, ApplicationMetricsSource):
                return source
            return None

    def create_custom_source(self, name: str) -> CustomMetricsSource:
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
