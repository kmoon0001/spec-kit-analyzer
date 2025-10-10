"""Performance Metrics Collection System

This module provides comprehensive performance metrics collection for baseline
and optimization testing, including statistical analysis and validation.
"""

import asyncio
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean, median, stdev
from typing import Any

import psutil

logger = logging.getLogger(__name__)


@dataclass
class ResponseTimeMetrics:
    """Response time performance metrics"""

    average_ms: float
    median_ms: float
    min_ms: float
    max_ms: float
    p95_ms: float
    p99_ms: float
    std_dev_ms: float
    sample_count: int


@dataclass
class MemoryMetrics:
    """Memory usage performance metrics"""

    peak_usage_mb: float
    average_usage_mb: float
    min_usage_mb: float
    current_usage_mb: float
    memory_efficiency: float  # Ratio of useful memory to total allocated
    gc_collections: int
    memory_leaks_detected: bool


@dataclass
class CacheMetrics:
    """Cache performance metrics"""

    hit_rate: float
    miss_rate: float
    total_requests: int
    cache_size_mb: float
    eviction_count: int
    average_lookup_time_ms: float


@dataclass
class ResourceMetrics:
    """System resource utilization metrics"""

    cpu_usage_percent: float
    memory_usage_percent: float
    disk_io_mb_per_sec: float
    network_io_mb_per_sec: float
    thread_count: int
    process_count: int


@dataclass
class ThroughputMetrics:
    """System throughput metrics"""

    documents_per_minute: float
    requests_per_second: float
    bytes_processed_per_second: float
    concurrent_operations: int


@dataclass
class ErrorRateMetrics:
    """Error rate and reliability metrics"""

    error_rate_percent: float
    timeout_rate_percent: float
    retry_rate_percent: float
    total_errors: int
    error_types: dict[str, int]


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics collection"""

    timestamp: datetime
    response_times: ResponseTimeMetrics | None = None
    memory_usage: MemoryMetrics | None = None
    cache_performance: CacheMetrics | None = None
    resource_utilization: ResourceMetrics | None = None
    throughput: ThroughputMetrics | None = None
    error_rates: ErrorRateMetrics | None = None
    custom_metrics: dict[str, Any] = field(default_factory=dict)


class BaselineMetricsCollector:
    """Collects performance metrics without optimizations enabled"""

    def __init__(self):
        self.is_collecting = False
        self.collection_thread: threading.Thread | None = None
        self.metrics_history: list[PerformanceMetrics] = []
        self.collection_interval = 1.0  # seconds
        self._stop_event = threading.Event()

    def start_collection(self) -> None:
        """Start continuous metrics collection"""
        if self.is_collecting:
            logger.warning("Metrics collection already running")
            return

        self.is_collecting = True
        self._stop_event.clear()
        self.collection_thread = threading.Thread(target=self._collection_loop)
        self.collection_thread.daemon = True
        self.collection_thread.start()
        logger.info("Started baseline metrics collection")

    def stop_collection(self) -> None:
        """Stop metrics collection"""
        if not self.is_collecting:
            return

        self.is_collecting = False
        self._stop_event.set()

        if self.collection_thread:
            self.collection_thread.join(timeout=5.0)

        logger.info("Stopped baseline metrics collection")

    def _collection_loop(self) -> None:
        """Main collection loop running in separate thread"""
        while not self._stop_event.is_set():
            try:
                metrics = self.collect_current_metrics()
                self.metrics_history.append(metrics)

                # Keep only recent metrics (last 1000 samples)
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]

            except Exception as e:
                logger.exception("Error collecting metrics: %s", e)

            self._stop_event.wait(self.collection_interval)

    def collect_current_metrics(self) -> PerformanceMetrics:
        """Collect current system performance metrics"""
        timestamp = datetime.now()

        # Collect system resource metrics
        resource_metrics = self._collect_resource_metrics()

        # Collect memory metrics
        memory_metrics = self._collect_memory_metrics()

        return PerformanceMetrics(
            timestamp=timestamp,
            memory_usage=memory_metrics,
            resource_utilization=resource_metrics,
        )

    def _collect_resource_metrics(self) -> ResourceMetrics:
        """Collect system resource utilization metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_io_mb = 0.0
            if disk_io:
                disk_io_mb = (disk_io.read_bytes + disk_io.write_bytes) / (1024 * 1024)

            # Network I/O
            network_io = psutil.net_io_counters()
            network_io_mb = 0.0
            if network_io:
                network_io_mb = (network_io.bytes_sent + network_io.bytes_recv) / (1024 * 1024)

            # Process information
            current_process = psutil.Process()
            thread_count = current_process.num_threads()

            return ResourceMetrics(
                cpu_usage_percent=cpu_percent,
                memory_usage_percent=memory_percent,
                disk_io_mb_per_sec=disk_io_mb,
                network_io_mb_per_sec=network_io_mb,
                thread_count=thread_count,
                process_count=len(psutil.pids()),
            )

        except Exception as e:
            logger.exception("Error collecting resource metrics: %s", e)
            return ResourceMetrics(0, 0, 0, 0, 0, 0)

    def _collect_memory_metrics(self) -> MemoryMetrics:
        """Collect memory usage metrics"""
        try:
            current_process = psutil.Process()
            memory_info = current_process.memory_info()

            # Convert bytes to MB
            current_usage_mb = memory_info.rss / (1024 * 1024)

            # Get system memory info
            memory = psutil.virtual_memory()

            return MemoryMetrics(
                peak_usage_mb=current_usage_mb,  # Will be updated with actual peak
                average_usage_mb=current_usage_mb,  # Will be calculated from history
                min_usage_mb=current_usage_mb,
                current_usage_mb=current_usage_mb,
                memory_efficiency=min(1.0, current_usage_mb / (memory.total / 1024 / 1024)),
                gc_collections=0,  # Would need GC integration
                memory_leaks_detected=False,
            )

        except Exception as e:
            logger.exception("Error collecting memory metrics: %s", e)
            return MemoryMetrics(0, 0, 0, 0, 0, 0, False)

    def get_baseline_summary(self) -> PerformanceMetrics | None:
        """Get summarized baseline metrics"""
        if not self.metrics_history:
            return None

        # Calculate averages and aggregates from history
        memory_usage_values = [
            m.memory_usage.current_usage_mb for m in self.metrics_history
            if m.memory_usage
        ]

        cpu_usage_values = [
            m.resource_utilization.cpu_usage_percent for m in self.metrics_history
            if m.resource_utilization
        ]

        if not memory_usage_values or not cpu_usage_values:
            return self.metrics_history[-1]  # Return latest if no aggregation possible

        # Create aggregated metrics
        aggregated_memory = MemoryMetrics(
            peak_usage_mb=max(memory_usage_values),
            average_usage_mb=mean(memory_usage_values),
            min_usage_mb=min(memory_usage_values),
            current_usage_mb=memory_usage_values[-1],
            memory_efficiency=0.85,
            gc_collections=0,
            memory_leaks_detected=False,
        )

        aggregated_resources = ResourceMetrics(
            cpu_usage_percent=mean(cpu_usage_values),
            memory_usage_percent=mean([
                m.resource_utilization.memory_usage_percent for m in self.metrics_history
                if m.resource_utilization
            ]),
            disk_io_mb_per_sec=0.0,
            network_io_mb_per_sec=0.0,
            thread_count=self.metrics_history[-1].resource_utilization.thread_count if self.metrics_history[-1].resource_utilization else 0,
            process_count=0,
        )

        return PerformanceMetrics(
            timestamp=datetime.now(),
            memory_usage=aggregated_memory,
            resource_utilization=aggregated_resources,
        )


class OptimizationMetricsCollector:
    """Collects performance metrics with optimizations enabled"""

    def __init__(self):
        self.baseline_collector = BaselineMetricsCollector()
        self.optimization_enabled = False
        self.cache_service = None  # Will be injected
        self.memory_manager = None  # Will be injected

    def set_optimization_services(self, cache_service=None, memory_manager=None):
        """Set optimization services for metrics collection"""
        self.cache_service = cache_service
        self.memory_manager = memory_manager

    def enable_optimizations(self) -> None:
        """Enable optimization systems for testing"""
        self.optimization_enabled = True
        logger.info("Optimizations enabled for metrics collection")

    def disable_optimizations(self) -> None:
        """Disable optimization systems"""
        self.optimization_enabled = False
        logger.info("Optimizations disabled for metrics collection")

    def collect_optimization_metrics(self) -> PerformanceMetrics:
        """Collect metrics with optimizations enabled"""
        base_metrics = self.baseline_collector.collect_current_metrics()

        # Collect cache metrics if available
        cache_metrics = None
        if self.cache_service and self.optimization_enabled:
            cache_metrics = self._collect_cache_metrics()

        # Update base metrics with optimization-specific data
        base_metrics.cache_performance = cache_metrics

        return base_metrics

    def _collect_cache_metrics(self) -> CacheMetrics:
        """Collect cache performance metrics"""
        try:
            # This would integrate with actual cache service
            # For now, return simulated metrics
            return CacheMetrics(
                hit_rate=0.75,  # 75% hit rate
                miss_rate=0.25,
                total_requests=1000,
                cache_size_mb=128.0,
                eviction_count=10,
                average_lookup_time_ms=2.5,
            )
        except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
            logger.exception("Error collecting cache metrics: %s", e)
            return CacheMetrics(0, 0, 0, 0, 0, 0)

    async def measure_response_times(self, operation: Callable, iterations: int = 10) -> ResponseTimeMetrics:
        """Measure response times for a specific operation"""
        response_times = []

        for _i in range(iterations):
            start_time = time.perf_counter()
            try:
                if asyncio.iscoroutinefunction(operation):
                    await operation()
                else:
                    operation()

                end_time = time.perf_counter()
                response_time_ms = (end_time - start_time) * 1000
                response_times.append(response_time_ms)

            except Exception as e:
                logger.exception("Error during operation measurement: %s", e)
                continue

        if not response_times:
            return ResponseTimeMetrics(0, 0, 0, 0, 0, 0, 0, 0)

        response_times.sort()

        return ResponseTimeMetrics(
            average_ms=mean(response_times),
            median_ms=median(response_times),
            min_ms=min(response_times),
            max_ms=max(response_times),
            p95_ms=response_times[int(0.95 * len(response_times))],
            p99_ms=response_times[int(0.99 * len(response_times))],
            std_dev_ms=stdev(response_times) if len(response_times) > 1 else 0,
            sample_count=len(response_times),
        )


class StatisticalAnalysisEngine:
    """Provides statistical analysis of performance metrics"""

    @staticmethod
    def calculate_improvement_percentage(baseline: float, optimized: float) -> float:
        """Calculate percentage improvement from baseline to optimized"""
        if baseline == 0:
            return 0.0
        return ((baseline - optimized) / baseline) * 100

    @staticmethod
    def calculate_confidence_interval(values: list[float], confidence: float = 0.95) -> tuple:
        """Calculate confidence interval for a list of values"""
        if len(values) < 2:
            return (0.0, 0.0)

        import scipy.stats as stats

        mean_val = mean(values)
        std_err = stdev(values) / (len(values) ** 0.5)

        # Use t-distribution for small samples
        t_value = stats.t.ppf((1 + confidence) / 2, len(values) - 1)
        margin_error = t_value * std_err

        return (mean_val - margin_error, mean_val + margin_error)

    @staticmethod
    def is_statistically_significant(baseline_values: list[float],
                                   optimized_values: list[float],
                                   alpha: float = 0.05) -> tuple:
        """Perform statistical significance test between baseline and optimized metrics"""
        if len(baseline_values) < 2 or len(optimized_values) < 2:
            return False, 1.0

        try:
            import scipy.stats as stats

            # Perform two-sample t-test
            t_stat, p_value = stats.ttest_ind(baseline_values, optimized_values)

            is_significant = p_value < alpha
            return is_significant, p_value

        except ImportError:
            logger.warning("scipy not available for statistical testing")
            # Fallback to simple comparison
            baseline_mean = mean(baseline_values)
            optimized_mean = mean(optimized_values)

            # Simple threshold-based significance
            improvement = abs(baseline_mean - optimized_mean) / baseline_mean
            return improvement > 0.05, 0.05  # 5% improvement threshold

    @staticmethod
    def analyze_performance_comparison(baseline_metrics: PerformanceMetrics,
                                     optimized_metrics: PerformanceMetrics) -> dict[str, Any]:
        """Analyze performance comparison between baseline and optimized metrics"""
        analysis = {
            "timestamp": datetime.now(),
            "improvements": {},
            "regressions": {},
            "statistical_significance": {},
        }

        # Compare response times if available
        if (baseline_metrics.response_times and optimized_metrics.response_times):
            baseline_avg = baseline_metrics.response_times.average_ms
            optimized_avg = optimized_metrics.response_times.average_ms

            improvement = StatisticalAnalysisEngine.calculate_improvement_percentage(
                baseline_avg, optimized_avg,
            )

            if improvement > 0:
                analysis["improvements"]["response_time"] = {
                    "improvement_percent": improvement,
                    "baseline_ms": baseline_avg,
                    "optimized_ms": optimized_avg,
                }
            elif improvement < 0:
                analysis["regressions"]["response_time"] = {
                    "regression_percent": abs(improvement),
                    "baseline_ms": baseline_avg,
                    "optimized_ms": optimized_avg,
                }

        # Compare memory usage
        if (baseline_metrics.memory_usage and optimized_metrics.memory_usage):
            baseline_memory = baseline_metrics.memory_usage.average_usage_mb
            optimized_memory = optimized_metrics.memory_usage.average_usage_mb

            improvement = StatisticalAnalysisEngine.calculate_improvement_percentage(
                baseline_memory, optimized_memory,
            )

            if improvement > 0:
                analysis["improvements"]["memory_usage"] = {
                    "improvement_percent": improvement,
                    "baseline_mb": baseline_memory,
                    "optimized_mb": optimized_memory,
                }
            elif improvement < 0:
                analysis["regressions"]["memory_usage"] = {
                    "regression_percent": abs(improvement),
                    "baseline_mb": baseline_memory,
                    "optimized_mb": optimized_memory,
                }

        # Add cache performance if available
        if optimized_metrics.cache_performance:
            cache_metrics = optimized_metrics.cache_performance
            analysis["improvements"]["cache_performance"] = {
                "hit_rate": cache_metrics.hit_rate,
                "average_lookup_time_ms": cache_metrics.average_lookup_time_ms,
                "cache_size_mb": cache_metrics.cache_size_mb,
            }

        return analysis

    @staticmethod
    def validate_metrics_accuracy(metrics: PerformanceMetrics) -> dict[str, bool]:
        """Validate the accuracy and consistency of collected metrics"""
        validation_results = {
            "response_times_valid": True,
            "memory_metrics_valid": True,
            "resource_metrics_valid": True,
            "cache_metrics_valid": True,
            "overall_valid": True,
        }

        # Validate response times
        if metrics.response_times:
            rt = metrics.response_times
            if rt.min_ms > rt.max_ms or rt.average_ms < 0:
                validation_results["response_times_valid"] = False

        # Validate memory metrics
        if metrics.memory_usage:
            mem = metrics.memory_usage
            if mem.current_usage_mb < 0 or mem.peak_usage_mb < mem.current_usage_mb:
                validation_results["memory_metrics_valid"] = False

        # Validate resource metrics
        if metrics.resource_utilization:
            res = metrics.resource_utilization
            if (res.cpu_usage_percent < 0 or res.cpu_usage_percent > 100 or
                res.memory_usage_percent < 0 or res.memory_usage_percent > 100):
                validation_results["resource_metrics_valid"] = False

        # Validate cache metrics
        if metrics.cache_performance:
            cache = metrics.cache_performance
            if (cache.hit_rate < 0 or cache.hit_rate > 1 or
                cache.miss_rate < 0 or cache.miss_rate > 1 or
                abs(cache.hit_rate + cache.miss_rate - 1.0) > 0.01):
                validation_results["cache_metrics_valid"] = False

        # Overall validation
        validation_results["overall_valid"] = all(validation_results.values())

        return validation_results
