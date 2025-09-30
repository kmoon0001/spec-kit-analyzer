"""
Performance Integration Service - Connects performance management to the main application.
Provides a unified interface for performance monitoring and optimization.
"""

import logging
from typing import Dict, Any, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

logger = logging.getLogger(__name__)


class PerformanceIntegrationService(QObject):
    """
    Service that integrates performance management throughout the application.
    Provides centralized performance monitoring and optimization triggers.
    """

    # Signals for performance events
    performance_warning = pyqtSignal(str, str)  # level, message
    memory_pressure = pyqtSignal(float)  # memory percentage
    profile_changed = pyqtSignal(str)  # new profile name
    optimization_completed = pyqtSignal(dict)  # optimization results

    def __init__(self):
        super().__init__()
        self.performance_manager = None
        self.cache_service = None
        self.monitoring_enabled = True
        self.warning_callbacks = []

        # Initialize performance components
        self._initialize_performance_manager()
        self._initialize_cache_service()

        # Setup monitoring timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._check_performance)
        self.monitor_timer.start(10000)  # Check every 10 seconds

        logger.info("Performance integration service initialized")

    def _initialize_performance_manager(self):
        """Initialize the performance manager."""
        try:
            from .performance_manager import performance_manager

            self.performance_manager = performance_manager
            logger.info("Performance manager connected")
        except ImportError as e:
            logger.warning(f"Performance manager not available: {e}")

    def _initialize_cache_service(self):
        """Initialize the cache service."""
        try:
            from .cache_service import cache_service

            self.cache_service = cache_service
            logger.info("Cache service connected")
        except ImportError as e:
            logger.warning(f"Cache service not available: {e}")

    def get_performance_status(self) -> Dict[str, Any]:
        """Get comprehensive performance status."""
        status = {
            "timestamp": self._get_current_timestamp(),
            "monitoring_enabled": self.monitoring_enabled,
            "performance_manager_available": self.performance_manager is not None,
            "cache_service_available": self.cache_service is not None,
        }

        if self.performance_manager:
            try:
                memory_stats = self.performance_manager.get_memory_usage()
                status.update(
                    {
                        "current_profile": self.performance_manager.current_profile.value,
                        "system_memory_percent": memory_stats.get(
                            "system_used_percent", 0
                        ),
                        "process_memory_mb": memory_stats.get("process_memory_mb", 0),
                        "gpu_available": self.performance_manager.system_info.get(
                            "cuda_available", False
                        ),
                    }
                )
            except Exception as e:
                logger.error(f"Error getting performance manager status: {e}")
                status["performance_error"] = str(e)

        if self.cache_service:
            try:
                from .cache_service import get_cache_stats

                cache_stats = get_cache_stats()
                status.update(
                    {
                        "cache_memory_mb": cache_stats.get("memory_usage_mb", 0),
                        "cache_entries": cache_stats.get("total_entries", 0),
                        "cache_hit_rate": self._get_cache_hit_rate(),
                    }
                )
            except Exception as e:
                logger.error(f"Error getting cache status: {e}")
                status["cache_error"] = str(e)

        return status

    def optimize_for_analysis(self) -> Dict[str, Any]:
        """Optimize system performance before running analysis."""
        optimization_results = {
            "cache_cleanup": False,
            "memory_freed_mb": 0,
            "profile_adjusted": False,
            "recommendations": [],  # type: ignore
        }

        try:
            if self.performance_manager:
                # Check if we need to adjust performance profile
                memory_stats = self.performance_manager.get_memory_usage()
                memory_percent = memory_stats.get("system_used_percent", 0)

                if memory_percent > 80:
                    # High memory usage - recommend conservative settings
                    optimization_results["recommendations"].append(
                        "High memory usage detected. Consider switching to Conservative profile."
                    )

                    # Trigger adaptive cleanup
                    self.performance_manager.adaptive_cleanup()
                    optimization_results["cache_cleanup"] = True

            if self.cache_service:
                # Clean up cache if needed
                from .cache_service import cleanup_all_caches, get_cache_stats

                cache_stats_before = get_cache_stats()
                cleanup_all_caches()
                cache_stats_after = get_cache_stats()

                memory_freed = cache_stats_before.get(
                    "memory_usage_mb", 0
                ) - cache_stats_after.get("memory_usage_mb", 0)
                if memory_freed > 0:
                    optimization_results["memory_freed_mb"] = memory_freed
                    optimization_results["cache_cleanup"] = True

            # Emit optimization completed signal
            self.optimization_completed.emit(optimization_results)

            logger.info(f"Performance optimization completed: {optimization_results}")
            return optimization_results

        except Exception as e:
            logger.error(f"Error during performance optimization: {e}")
            optimization_results["error"] = str(e)
            return optimization_results

    def register_warning_callback(self, callback: Callable[[str, str], None]):
        """Register a callback for performance warnings."""
        self.warning_callbacks.append(callback)

    def _check_performance(self):
        """Periodic performance check."""
        if not self.monitoring_enabled or not self.performance_manager:
            return

        try:
            memory_stats = self.performance_manager.get_memory_usage()
            memory_percent = memory_stats.get("system_used_percent", 0)

            # Emit memory pressure signal
            self.memory_pressure.emit(memory_percent)

            # Check for warning conditions
            if memory_percent > 90:
                self._emit_warning(
                    "critical", f"Critical memory usage: {memory_percent:.1f}%"
                )
            elif memory_percent > 80:
                self._emit_warning(
                    "warning", f"High memory usage: {memory_percent:.1f}%"
                )

            # Check process memory
            process_memory = memory_stats.get("process_memory_mb", 0)
            if process_memory > 2048:  # 2GB
                self._emit_warning(
                    "warning", f"High process memory usage: {process_memory:.1f} MB"
                )

        except Exception as e:
            logger.error(f"Error in performance check: {e}")

    def _emit_warning(self, level: str, message: str):
        """Emit performance warning."""
        self.performance_warning.emit(level, message)

        # Call registered callbacks
        for callback in self.warning_callbacks:
            try:
                callback(level, message)
            except Exception as e:
                logger.error(f"Error in warning callback: {e}")

    def _get_current_timestamp(self) -> str:
        """Get current timestamp for status."""
        from datetime import datetime

        return datetime.now().isoformat()

    def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate if available."""
        try:
            from .cache_integration_service import cache_integration

            stats = cache_integration.get_cache_performance_stats()
            return stats.get("hit_rate_percent", 0.0)
        except ImportError:
            return 0.0

    def set_monitoring_enabled(self, enabled: bool):
        """Enable or disable performance monitoring."""
        self.monitoring_enabled = enabled
        if enabled:
            self.monitor_timer.start(10000)
        else:
            self.monitor_timer.stop()

        logger.info(f"Performance monitoring {'enabled' if enabled else 'disabled'}")

    def cleanup(self):
        """Clean up resources."""
        if self.monitor_timer:
            self.monitor_timer.stop()

        self.warning_callbacks.clear()
        logger.info("Performance integration service cleaned up")


# Global performance integration service
performance_integration = PerformanceIntegrationService()


def get_performance_integration() -> PerformanceIntegrationService:
    """Get the global performance integration service."""
    return performance_integration


def optimize_for_analysis() -> Dict[str, Any]:
    """Convenience function to optimize performance before analysis."""
    return performance_integration.optimize_for_analysis()


def get_performance_status() -> Dict[str, Any]:
    """Convenience function to get current performance status."""
    return performance_integration.get_performance_status()
