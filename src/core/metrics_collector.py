"""
Metrics Collector for Performance Monitoring

This module provides comprehensive metric collection from various system
components including system resources, application metrics, and custom sources.
"""

import logging
import psutil  # type: ignore[import-untyped]
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

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
    tags: Dict[str, str]
    metadata: Dict[str, Any]


class MetricSource(ABC):
    """Abstract base class for metric sources."""
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of this metric source."""
        pass
    
    @abstractmethod
    def collect_metrics(self) -> List[PerformanceMetric]:
        """Collect metrics from this source."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this metric source is available."""
        pass
    
    def cleanup(self) -> None:
        """Cleanup resources used by this source."""
        pass


class SystemMetricsSource(MetricSource):
    """Collects system-level metrics using psutil."""
    
    def __init__(self):
        self._last_cpu_times: Optional[Any] = None
        self._last_network_io: Optional[Any] = None
        self._last_disk_io: Optional[Any] = None
        self._collection_time: Optional[datetime] = None
    
    def get_source_name(self) -> str:
        return "system"
    
    def collect_metrics(self) -> List[PerformanceMetric]:
        """Collect system metrics."""
        metrics = []
        timestamp = datetime.now()
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            metrics.append(PerformanceMetric(
                timestamp=timestamp,
                name="cpu_usage_percent",
                value=cpu_percent,
                unit="percent",
                metric_type=MetricType.GAUGE,
                source=self.get_source_name(),
                tags={"type": "cpu"},
                metadata={"cpu_count": cpu_count}
            ))
            
            if cpu_freq:
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    name="cpu_frequency_mhz",
                    value=cpu_freq.current,
                    unit="mhz",
                    metric_type=MetricType.GAUGE,
                    source=self.get_source_name(),
                    tags={"type": "cpu"},
                    metadata={"max_freq": cpu_freq.max, "min_freq": cpu_freq.min}
                ))
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            metrics.extend([
                PerformanceMetric(
                    timestamp=timestamp,
                    name="memory_usage_percent",
                    value=memory.percent,
                    unit="percent",
                    metric_type=MetricType.GAUGE,
                    source=self.get_source_name(),
                    tags={"type": "memory"},
                    metadata={"total_mb": memory.total // (1024 * 1024)}
                ),
                PerformanceMetric(
                    timestamp=timestamp,
                    name="memory_available_mb",
                    value=memory.available // (1024 * 1024),
                    unit="mb",
                    metric_type=MetricType.GAUGE,
                    source=self.get_source_name(),
                    tags={"type": "memory"},
                    metadata={}
                ),
                PerformanceMetric(
                    timestamp=timestamp,
                    name="swap_usage_percent",
                    value=swap.percent,
                    unit="percent",
                    metric_type=MetricType.GAUGE,
                    source=self.get_source_name(),
                    tags={"type": "memory", "subtype": "swap"},
                    metadata={"total_mb": swap.total // (1024 * 1024)}
                )
            ])
            
            # Disk metrics
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            metrics.append(PerformanceMetric(
                timestamp=timestamp,
                name="disk_usage_percent",
                value=(disk_usage.used / disk_usage.total) * 100,
                unit="percent",
                metric_type=MetricType.GAUGE,
                source=self.get_source_name(),
                tags={"type": "disk"},
                metadata={"total_gb": disk_usage.total // (1024 * 1024 * 1024)}
            ))
            
            if disk_io and self._last_disk_io and self._collection_time:
                time_delta = (timestamp - self._collection_time).total_seconds()
                if time_delta > 0:
                    read_rate = (disk_io.read_bytes - self._last_disk_io.read_bytes) / time_delta
                    write_rate = (disk_io.write_bytes - self._last_disk_io.write_bytes) / time_delta
                    
                    metrics.extend([
                        PerformanceMetric(
                            timestamp=timestamp,
                            name="disk_read_rate_bps",
                            value=read_rate,
                            unit="bytes_per_second",
                            metric_type=MetricType.GAUGE,
                            source=self.get_source_name(),
                            tags={"type": "disk", "operation": "read"},
                            metadata={}
                        ),
                        PerformanceMetric(
                            timestamp=timestamp,
                            name="disk_write_rate_bps",
                            value=write_rate,
                            unit="bytes_per_second",
                            metric_type=MetricType.GAUGE,
                            source=self.get_source_name(),
                            tags={"type": "disk", "operation": "write"},
                            metadata={}
                        )
                    ])
            
            # Network metrics
            network_io = psutil.net_io_counters()
            
            if network_io and self._last_network_io and self._collection_time:
                time_delta = (timestamp - self._collection_time).total_seconds()
                if time_delta > 0:
                    bytes_sent_rate = (network_io.bytes_sent - self._last_network_io.bytes_sent) / time_delta
                    bytes_recv_rate = (network_io.bytes_recv - self._last_network_io.bytes_recv) / time_delta
                    
                    metrics.extend([
                        PerformanceMetric(
                            timestamp=timestamp,
                            name="network_sent_rate_bps",
                            value=bytes_sent_rate,
                            unit="bytes_per_second",
                            metric_type=MetricType.GAUGE,
                            source=self.get_source_name(),
                            tags={"type": "network", "direction": "sent"},
                            metadata={}
                        ),
                        PerformanceMetric(
                            timestamp=timestamp,
                            name="network_recv_rate_bps",
                            value=bytes_recv_rate,
                            unit="bytes_per_second",
                            metric_type=MetricType.GAUGE,
                            source=self.get_source_name(),
                            tags={"type": "network", "direction": "received"},
                            metadata={}
                        )
                    ])
            
            # Update state for next collection
            self._last_disk_io = disk_io
            self._last_network_io = network_io
            self._collection_time = timestamp
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
        
        return metrics
    
    def is_available(self) -> bool:
        """Check if system metrics are available."""
        try:
            psutil.cpu_percent()
            return True
        except Exception:
            return False


class ApplicationMetricsSource(MetricSource):
    """Collects application-specific metrics."""
    
    def __init__(self):
        self._response_times: List[float] = []
        self._error_counts: Dict[str, int] = {}
        self._request_counts: Dict[str, int] = {}
        self._lock = threading.Lock()
    
    def get_source_name(self) -> str:
        return "application"
    
    def collect_metrics(self) -> List[PerformanceMetric]:
        """Collect application metrics."""
        metrics = []
        timestamp = datetime.now()
        
        with self._lock:
            # Response time metrics
            if self._response_times:
                avg_response_time = sum(self._response_times) / len(self._response_times)
                max_response_time = max(self._response_times)
                min_response_time = min(self._response_times)
                
                metrics.extend([
                    PerformanceMetric(
                        timestamp=timestamp,
                        name="response_time_avg_ms",
                        value=avg_response_time,
                        unit="milliseconds",
                        metric_type=MetricType.GAUGE,
                        source=self.get_source_name(),
                        tags={"type": "performance"},
                        metadata={"sample_count": len(self._response_times)}
                    ),
                    PerformanceMetric(
                        timestamp=timestamp,
                        name="response_time_max_ms",
                        value=max_response_time,
                        unit="milliseconds",
                        metric_type=MetricType.GAUGE,
                        source=self.get_source_name(),
                        tags={"type": "performance"},
                        metadata={}
                    ),
                    PerformanceMetric(
                        timestamp=timestamp,
                        name="response_time_min_ms",
                        value=min_response_time,
                        unit="milliseconds",
                        metric_type=MetricType.GAUGE,
                        source=self.get_source_name(),
                        tags={"type": "performance"},
                        metadata={}
                    )
                ])
                
                # Clear response times after collection
                self._response_times.clear()
            
            # Error rate metrics
            total_requests = sum(self._request_counts.values())
            total_errors = sum(self._error_counts.values())
            
            if total_requests > 0:
                error_rate = (total_errors / total_requests) * 100
                
                metrics.append(PerformanceMetric(
                    timestamp=timestamp,
                    name="error_rate_percent",
                    value=error_rate,
                    unit="percent",
                    metric_type=MetricType.GAUGE,
                    source=self.get_source_name(),
                    tags={"type": "errors"},
                    metadata={"total_requests": total_requests, "total_errors": total_errors}
                ))
            
            # Throughput metrics
            metrics.append(PerformanceMetric(
                timestamp=timestamp,
                name="requests_per_minute",
                value=total_requests,  # This would be calculated over time in a real implementation
                unit="requests_per_minute",
                metric_type=MetricType.GAUGE,
                source=self.get_source_name(),
                tags={"type": "throughput"},
                metadata={}
            ))
            
            # Clear counters after collection
            self._error_counts.clear()
            self._request_counts.clear()
        
        return metrics
    
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
    
    def is_available(self) -> bool:
        """Application metrics are always available."""
        return True


class CustomMetricsSource(MetricSource):
    """Allows registration of custom metrics."""
    
    def __init__(self, name: str):
        self.name = name
        self._metrics: List[PerformanceMetric] = []
        self._lock = threading.Lock()
    
    def get_source_name(self) -> str:
        return f"custom_{self.name}"
    
    def collect_metrics(self) -> List[PerformanceMetric]:
        """Collect custom metrics."""
        with self._lock:
            metrics = self._metrics.copy()
            self._metrics.clear()
            return metrics
    
    def add_metric(self, metric: PerformanceMetric) -> None:
        """Add a custom metric."""
        with self._lock:
            self._metrics.append(metric)
    
    def is_available(self) -> bool:
        """Custom metrics are always available."""
        return True


class MetricsCollector:
    """Collects performance metrics from various sources."""
    
    def __init__(self, config):
        """Initialize metrics collector.
        
        Args:
            config: Monitoring configuration
        """
        self.config = config
        self._sources: Dict[str, MetricSource] = {}
        self._lock = threading.RLock()
        
        # Initialize default sources
        self._initialize_default_sources()
        
        logger.info(f"Metrics collector initialized with {len(self._sources)} sources")
    
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
                logger.warning(f"Metric source '{source_name}' is not available")
                return False
            
            with self._lock:
                if source_name in self._sources:
                    logger.warning(f"Metric source '{source_name}' already registered")
                    return False
                
                self._sources[source_name] = source
            
            logger.info(f"Registered metric source: {source_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register metric source: {e}")
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
                    logger.warning(f"Metric source '{source_name}' not found")
                    return False
                
                source = self._sources.pop(source_name)
                source.cleanup()
            
            logger.info(f"Unregistered metric source: {source_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister metric source '{source_name}': {e}")
            return False
    
    def collect_all_metrics(self) -> List[Dict[str, Any]]:
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
                            'timestamp': metric.timestamp.isoformat(),
                            'name': metric.name,
                            'value': metric.value,
                            'unit': metric.unit,
                            'type': metric.metric_type.value,
                            'source': metric.source,
                            'tags': metric.tags,
                            'metadata': metric.metadata
                        }
                        all_metrics.append(metric_dict)
                
            except Exception as e:
                logger.error(f"Error collecting metrics from source '{source_name}': {e}")
        
        logger.debug(f"Collected {len(all_metrics)} metrics from {len(sources_to_collect)} sources")
        return all_metrics
    
    def collect_metrics_from_source(self, source_name: str) -> List[Dict[str, Any]]:
        """Collect metrics from a specific source.
        
        Args:
            source_name: Name of source to collect from
            
        Returns:
            List of metric dictionaries from the specified source
        """
        with self._lock:
            if source_name not in self._sources:
                logger.warning(f"Metric source '{source_name}' not found")
                return []
            
            source = self._sources[source_name]
        
        try:
            if not source.is_available():
                logger.warning(f"Metric source '{source_name}' is not available")
                return []
            
            metrics = source.collect_metrics()
            
            # Convert to dictionaries
            metric_dicts = []
            for metric in metrics:
                metric_dict = {
                    'timestamp': metric.timestamp.isoformat(),
                    'name': metric.name,
                    'value': metric.value,
                    'unit': metric.unit,
                    'type': metric.metric_type.value,
                    'source': metric.source,
                    'tags': metric.tags,
                    'metadata': metric.metadata
                }
                metric_dicts.append(metric_dict)
            
            return metric_dicts
            
        except Exception as e:
            logger.error(f"Error collecting metrics from source '{source_name}': {e}")
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
    
    def get_source_names(self) -> List[str]:
        """Get names of all registered sources.
        
        Returns:
            List of source names
        """
        with self._lock:
            return list(self._sources.keys())
    
    def get_source_status(self) -> Dict[str, bool]:
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
    
    def get_application_source(self) -> Optional[ApplicationMetricsSource]:
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
    
    def cleanup(self) -> None:
        """Cleanup collector resources."""
        with self._lock:
            for source in self._sources.values():
                try:
                    source.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up metric source: {e}")
            
            self._sources.clear()
        
        logger.debug("Metrics collector cleaned up")
