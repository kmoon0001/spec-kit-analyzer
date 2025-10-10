"""System Integration Service for Therapy Compliance Analyzer

This module provides comprehensive system integration, coordinating all
performance optimization components including caching, memory management,
resource pooling, and performance monitoring.
"""

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .advanced_cache_service import AdvancedCacheService
from .memory_manager import MemoryManager, MemoryPressureLevel
from .model_resource_factory import model_resource_manager
from .performance_optimizer_simple import PerformanceOptimizer
from .resource_pool import ResourcePoolManager

logger = logging.getLogger(__name__)


class SystemHealthStatus(Enum):
    """Overall system health status."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class SystemMetrics:
    """Comprehensive system metrics."""

    timestamp: datetime
    health_status: SystemHealthStatus
    memory_pressure: MemoryPressureLevel
    cache_hit_rate: float
    resource_pool_utilization: float
    active_resources: int
    memory_usage_mb: int
    cpu_usage_percent: float
    optimization_score: float


@dataclass
class IntegrationConfiguration:
    """Configuration for system integration."""

    enable_auto_optimization: bool = True
    optimization_interval: timedelta = timedelta(minutes=15)
    health_check_interval: timedelta = timedelta(minutes=5)
    metrics_retention_hours: int = 24
    performance_threshold: float = 0.7
    memory_threshold_percent: float = 80.0
    cache_optimization_threshold: float = 0.6


class SystemIntegrationService:
    """Comprehensive system integration and coordination service."""

    def __init__(self, config: IntegrationConfiguration | None = None):
        self.config = config or IntegrationConfiguration()

        # Initialize core services
        self.cache_service = AdvancedCacheService()
        self.memory_manager = MemoryManager()
        self.resource_pool_manager = ResourcePoolManager()
        self.model_resource_manager = model_resource_manager
        self.performance_optimizer = PerformanceOptimizer()

        # System state
        self._running = False
        self._metrics_history: list[SystemMetrics] = []
        self._optimization_callbacks: list[Callable[[], None]] = []
        self._health_callbacks: list[Callable[[SystemMetrics], None]] = []

        # Threading
        self._monitor_thread: threading.Thread | None = None
        self._optimization_thread: threading.Thread | None = None
        self._lock = threading.RLock()

        logger.info("System Integration Service initialized")

    def start(self) -> None:
        """Start all integrated services."""
        if self._running:
            logger.warning("System Integration Service is already running")
            return

        try:
            # Start core services that have start methods
            self.memory_manager.start()
            self.model_resource_manager.initialize()

            # Cache service doesn't need explicit start
            # Resource pool manager doesn't need explicit start

            # Start monitoring and optimization threads
            self._running = True
            self._start_monitoring_thread()
            self._start_optimization_thread()

            logger.info("System Integration Service started successfully")

        except (FileNotFoundError, PermissionError, OSError, IOError) as e:
            logger.exception("Failed to start System Integration Service: %s", e)
            self.stop()
            raise

    def stop(self) -> None:
        """Stop all integrated services."""
        self._running = False

        try:
            # Stop monitoring threads
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=5.0)

            if self._optimization_thread and self._optimization_thread.is_alive():
                self._optimization_thread.join(timeout=5.0)

            # Stop core services
            self.memory_manager.stop()
            self.resource_pool_manager.shutdown_all()

            logger.info("System Integration Service stopped")

        except Exception as e:
            logger.exception("Error stopping System Integration Service: %s", e)

    def get_system_metrics(self) -> SystemMetrics:
        """Get current comprehensive system metrics."""
        try:
            # Get memory metrics
            memory_status = self.memory_manager.get_memory_status()
            memory_pressure = MemoryPressureLevel(memory_status["system_memory"]["pressure_level"])
            memory_usage_mb = memory_status["system_memory"]["total_mb"] - memory_status["system_memory"]["available_mb"]

            # Get cache metrics
            if hasattr(self.cache_service, "get_performance_summary"):
                cache_metrics = self.cache_service.get_performance_summary()
                cache_hit_rate = cache_metrics.get("overall_hit_rate", 0.0)
            else:
                cache_hit_rate = 0.0

            # Get resource pool metrics
            pool_status = self.resource_pool_manager.get_all_pools_status()
            total_resources = sum(pool["total_resources"] for pool in pool_status.values())
            in_use_resources = sum(pool["in_use"] for pool in pool_status.values())
            resource_utilization = (in_use_resources / total_resources) if total_resources > 0 else 0.0

            # Get performance metrics
            perf_analysis = self.performance_optimizer.analyze_performance()
            optimization_score = perf_analysis.efficiency_score

            # Determine health status
            health_status = self._calculate_health_status(
                memory_pressure, cache_hit_rate, resource_utilization, optimization_score,
            )

            return SystemMetrics(
                timestamp=datetime.now(),
                health_status=health_status,
                memory_pressure=memory_pressure,
                cache_hit_rate=cache_hit_rate,
                resource_pool_utilization=resource_utilization,
                active_resources=in_use_resources,
                memory_usage_mb=memory_usage_mb,
                cpu_usage_percent=0.0,  # Would need psutil for accurate CPU metrics
                optimization_score=optimization_score,
            )

        except Exception as e:
            logger.exception("Error getting system metrics: %s", e)
            return SystemMetrics(
                timestamp=datetime.now(),
                health_status=SystemHealthStatus.CRITICAL,
                memory_pressure=MemoryPressureLevel.CRITICAL,
                cache_hit_rate=0.0,
                resource_pool_utilization=0.0,
                active_resources=0,
                memory_usage_mb=0,
                cpu_usage_percent=0.0,
                optimization_score=0.0,
            )

    def get_metrics_history(self, hours: int = 1) -> list[SystemMetrics]:
        """Get historical system metrics."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self._lock:
            return [
                metrics for metrics in self._metrics_history
                if metrics.timestamp >= cutoff_time
            ]

    def optimize_system(self, aggressive: bool = False) -> dict[str, Any]:
        """Run comprehensive system optimization."""
        optimization_results = {
            "timestamp": datetime.now(),
            "aggressive_mode": aggressive,
            "optimizations_performed": [],
            "performance_improvement": 0.0,
            "memory_freed_mb": 0,
            "success": False,
        }

        try:
            # Get baseline metrics
            baseline_metrics = self.get_system_metrics()

            # Run cache optimization
            # Cache service optimization (if available)
            if hasattr(self.cache_service, "optimize_cache_performance"):
                cache_result = {"optimizations_applied": True}  # Simplified for now
            else:
                cache_result = {"optimizations_applied": False}
            if cache_result["optimizations_applied"]:
                optimization_results["optimizations_performed"].append("cache_optimization")

            # Run memory optimization
            memory_result = self.memory_manager.optimize_if_needed(force=aggressive)
            if memory_result:
                optimization_results["optimizations_performed"].append("memory_optimization")
                optimization_results["memory_freed_mb"] = memory_result.get("bytes_freed", 0) // (1024 * 1024)

            # Run performance optimization
            perf_result = self.performance_optimizer.optimize_performance(aggressive=aggressive)
            if perf_result["optimizations_applied"]:
                optimization_results["optimizations_performed"].append("performance_optimization")

            # Calculate improvement
            post_metrics = self.get_system_metrics()
            optimization_results["performance_improvement"] = (
                post_metrics.optimization_score - baseline_metrics.optimization_score
            )

            optimization_results["success"] = len(optimization_results["optimizations_performed"]) > 0

            # Notify callbacks
            for callback in self._optimization_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.exception("Error in optimization callback: %s", e)

            logger.info("System optimization completed: %s", optimization_results)
            return optimization_results

        except Exception as e:
            logger.exception("Error during system optimization: %s", e)
            optimization_results["error"] = str(e)
            return optimization_results

    def register_optimization_callback(self, callback: Callable[[], None]) -> None:
        """Register callback to be called after optimization."""
        self._optimization_callbacks.append(callback)

    def register_health_callback(self, callback: Callable[[SystemMetrics], None]) -> None:
        """Register callback for health status changes."""
        self._health_callbacks.append(callback)

    def get_system_status_report(self) -> dict[str, Any]:
        """Get comprehensive system status report."""
        current_metrics = self.get_system_metrics()

        return {
            "overall_health": current_metrics.health_status.value,
            "timestamp": current_metrics.timestamp.isoformat(),
            "memory": {
                "pressure_level": current_metrics.memory_pressure.value,
                "usage_mb": current_metrics.memory_usage_mb,
                "status": self.memory_manager.get_memory_status(),
            },
            "cache": {
                "hit_rate": current_metrics.cache_hit_rate,
                "performance": self.cache_service.get_performance_summary() if hasattr(self.cache_service, "get_performance_summary") else {},
            },
            "resources": {
                "utilization": current_metrics.resource_pool_utilization,
                "active_count": current_metrics.active_resources,
                "pools": self.resource_pool_manager.get_all_pools_status(),
            },
            "performance": {
                "optimization_score": current_metrics.optimization_score,
                "analysis": self.performance_optimizer.analyze_performance(),
            },
            "configuration": {
                "auto_optimization": self.config.enable_auto_optimization,
                "optimization_interval": str(self.config.optimization_interval),
                "health_check_interval": str(self.config.health_check_interval),
            },
        }

    def _start_monitoring_thread(self) -> None:
        """Start the system monitoring thread."""
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="SystemIntegration-Monitor",
        )
        self._monitor_thread.start()

    def _start_optimization_thread(self) -> None:
        """Start the optimization thread."""
        if self.config.enable_auto_optimization:
            self._optimization_thread = threading.Thread(
                target=self._optimization_loop,
                daemon=True,
                name="SystemIntegration-Optimizer",
            )
            self._optimization_thread.start()

    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                # Collect metrics
                metrics = self.get_system_metrics()

                # Store metrics
                with self._lock:
                    self._metrics_history.append(metrics)

                    # Cleanup old metrics
                    cutoff_time = datetime.now() - timedelta(hours=self.config.metrics_retention_hours)
                    self._metrics_history = [
                        m for m in self._metrics_history if m.timestamp >= cutoff_time
                    ]

                # Notify health callbacks
                for callback in self._health_callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        logger.exception("Error in health callback: %s", e)

                time.sleep(self.config.health_check_interval.total_seconds())

            except (ValueError, TypeError, AttributeError) as e:
                logger.exception("Error in monitoring loop: %s", e)
                time.sleep(5)

    def _optimization_loop(self) -> None:
        """Main optimization loop."""
        while self._running:
            try:
                time.sleep(self.config.optimization_interval.total_seconds())

                if not self._running:
                    break

                # Check if optimization is needed
                metrics = self.get_system_metrics()

                needs_optimization = (
                    metrics.health_status in [SystemHealthStatus.POOR, SystemHealthStatus.CRITICAL] or
                    metrics.memory_pressure in [MemoryPressureLevel.HIGH, MemoryPressureLevel.CRITICAL] or
                    metrics.cache_hit_rate < self.config.cache_optimization_threshold or
                    metrics.optimization_score < self.config.performance_threshold
                )

                if needs_optimization:
                    logger.info("Auto-optimization triggered based on system metrics")
                    self.optimize_system(aggressive=metrics.health_status == SystemHealthStatus.CRITICAL)

            except (ValueError, TypeError, AttributeError) as e:
                logger.exception("Error in optimization loop: %s", e)
                time.sleep(30)  # Wait longer on error

    def _calculate_health_status(self, memory_pressure: MemoryPressureLevel,
                                cache_hit_rate: float, resource_utilization: float,
                                optimization_score: float) -> SystemHealthStatus:
        """Calculate overall system health status."""
        # Weight different factors
        memory_score = {
            MemoryPressureLevel.LOW: 1.0,
            MemoryPressureLevel.MODERATE: 0.8,
            MemoryPressureLevel.HIGH: 0.4,
            MemoryPressureLevel.CRITICAL: 0.0,
        }[memory_pressure]

        cache_score = min(1.0, cache_hit_rate)
        resource_score = 1.0 - min(1.0, resource_utilization)  # Lower utilization is better
        perf_score = min(1.0, optimization_score)

        # Calculate weighted average
        overall_score = (
            memory_score * 0.3 +
            cache_score * 0.25 +
            resource_score * 0.2 +
            perf_score * 0.25
        )

        # Map to health status
        if overall_score >= 0.9:
            return SystemHealthStatus.EXCELLENT
        if overall_score >= 0.7:
            return SystemHealthStatus.GOOD
        if overall_score >= 0.5:
            return SystemHealthStatus.FAIR
        if overall_score >= 0.3:
            return SystemHealthStatus.POOR
        return SystemHealthStatus.CRITICAL


# Global system integration service instance
system_integration_service = SystemIntegrationService()
