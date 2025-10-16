"""Performance Integration Service

Provides centralized performance monitoring and optimization triggers
for the Therapy Compliance Analyzer application.
"""

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

import requests
from requests.exceptions import HTTPError

logger = logging.getLogger(__name__)


class PerformanceIntegrationService:
    """Service that integrates performance management throughout the application.
    
    Provides centralized performance monitoring and optimization triggers.
    Converted from Qt signals to callback-based system for Electron compatibility.
    """

    def __init__(self) -> None:
        """Initialize the performance integration service."""
        # Callback lists for performance events
        self.performance_warning_callbacks: list[Callable[[str, str], None]] = []
        self.memory_pressure_callbacks: list[Callable[[float], None]] = []
        self.profile_changed_callbacks: list[Callable[[str], None]] = []
        self.optimization_completed_callbacks: list[Callable[[dict[str, Any]], None]] = []
        
        # Service references
        self.performance_manager: Any = None
        self.cache_service: Any = None
        self.monitoring_enabled: bool = True
        
        # Initialize performance components
        self._initialize_performance_manager()
        self._initialize_cache_service()
        
        logger.info("Performance integration service initialized")

    def _initialize_performance_manager(self) -> None:
        """Initialize the performance manager."""
        try:
            from src.core.performance_manager import performance_manager
            self.performance_manager = performance_manager
            logger.info("Performance manager connected")
        except ImportError as e:
            logger.warning("Performance manager not available: %s", e)

    def _initialize_cache_service(self) -> None:
        """Initialize the cache service."""
        try:
            from src.core.cache_service import cache_service
            self.cache_service = cache_service
            logger.info("Cache service connected")
        except ImportError as e:
            logger.warning("Cache service not available: %s", e)

    def get_performance_status(self) -> dict[str, Any]:
        """Get comprehensive performance status."""
        status: dict[str, Any] = {
            "timestamp": self._get_current_timestamp(),
            "monitoring_enabled": self.monitoring_enabled,
            "performance_manager_available": self.performance_manager is not None,
            "cache_service_available": self.cache_service is not None,
        }

        if self.performance_manager:
            try:
                memory_stats = self.performance_manager.get_memory_usage()
                status.update({
                    "current_profile": getattr(
                        self.performance_manager.current_profile, 'value', 'unknown'
                    ),
                    "system_memory_percent": memory_stats.get("system_used_percent", 0),
                    "process_memory_mb": memory_stats.get("process_memory_mb", 0),
                    "gpu_available": self.performance_manager.system_info.get(
                        "cuda_available", False
                    ),
                })
            except Exception as e:
                logger.exception("Error getting performance manager status: %s", e)
                status["performance_error"] = str(e)

        if self.cache_service:
            try:
                from src.core.cache_service import get_cache_stats
                cache_stats = get_cache_stats()
                status.update({
                    "cache_memory_mb": cache_stats.get("memory_usage_mb", 0),
                    "cache_entries": cache_stats.get("total_entries", 0),
                    "cache_hit_rate": self._get_cache_hit_rate(),
                })
            except Exception as e:
                logger.exception("Error getting cache status: %s", e)
                status["cache_error"] = str(e)

        return status

    def optimize_for_analysis(self) -> dict[str, Any]:
        """Optimize system performance before running analysis."""
        optimization_results: dict[str, Any] = {
            "cache_cleanup": False,
            "memory_freed_mb": 0,
            "recommendations": [],
            "profile_adjusted": False,
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
                    if hasattr(self.performance_manager, 'adaptive_cleanup'):
                        self.performance_manager.adaptive_cleanup()
                        optimization_results["cache_cleanup"] = True

            if self.cache_service:
                # Clean up cache if needed
                try:
                    from src.core.cache_service import cleanup_all_caches, get_cache_stats
                    
                    cache_stats_before = get_cache_stats()
                    cleanup_all_caches()
                    cache_stats_after = get_cache_stats()

                    memory_freed = (
                        cache_stats_before.get("memory_usage_mb", 0) - 
                        cache_stats_after.get("memory_usage_mb", 0)
                    )
                    if memory_freed > 0:
                        optimization_results["memory_freed_mb"] = memory_freed
                        optimization_results["cache_cleanup"] = True
                except ImportError:
                    logger.warning("Cache cleanup functions not available")

            # Emit optimization completed event
            self._emit_optimization_completed(optimization_results)

            logger.info("Performance optimization completed: %s", optimization_results)
            return optimization_results

        except Exception as e:
            logger.exception("Error during performance optimization: %s", e)
            optimization_results["error"] = str(e)
            return optimization_results

    def register_performance_warning_callback(
        self, callback: Callable[[str, str], None]
    ) -> None:
        """Register a callback for performance warnings."""
        self.performance_warning_callbacks.append(callback)

    def register_memory_pressure_callback(
        self, callback: Callable[[float], None]
    ) -> None:
        """Register a callback for memory pressure events."""
        self.memory_pressure_callbacks.append(callback)

    def register_profile_changed_callback(
        self, callback: Callable[[str], None]
    ) -> None:
        """Register a callback for profile change events."""
        self.profile_changed_callbacks.append(callback)

    def register_optimization_completed_callback(
        self, callback: Callable[[dict[str, Any]], None]
    ) -> None:
        """Register a callback for optimization completion events."""
        self.optimization_completed_callbacks.append(callback)

    def check_performance(self) -> None:
        """Manual performance check (replaces timer-based checking)."""
        if not self.monitoring_enabled or not self.performance_manager:
            return

        try:
            memory_stats = self.performance_manager.get_memory_usage()
            memory_percent = memory_stats.get("system_used_percent", 0)

            # Emit memory pressure event
            self._emit_memory_pressure(memory_percent)

            # Check for warning conditions
            if memory_percent > 90:
                self._emit_performance_warning("critical", f"Critical memory usage: {memory_percent}%")
            elif memory_percent > 80:
                self._emit_performance_warning("warning", f"High memory usage: {memory_percent}%")

            # Check process memory
            process_memory = memory_stats.get("process_memory_mb", 0)
            if process_memory > 2048:  # 2GB
                self._emit_performance_warning(
                    "warning", f"High process memory usage: {process_memory} MB"
                )

        except Exception as e:
            logger.exception("Error in performance check: %s", e)

    def _emit_performance_warning(self, level: str, message: str) -> None:
        """Emit performance warning to all registered callbacks."""
        for callback in self.performance_warning_callbacks:
            try:
                callback(level, message)
            except Exception as e:
                logger.exception("Error in performance warning callback: %s", e)

    def _emit_memory_pressure(self, memory_percent: float) -> None:
        """Emit memory pressure event to all registered callbacks."""
        for callback in self.memory_pressure_callbacks:
            try:
                callback(memory_percent)
            except Exception as e:
                logger.exception("Error in memory pressure callback: %s", e)

    def _emit_profile_changed(self, profile_name: str) -> None:
        """Emit profile changed event to all registered callbacks."""
        for callback in self.profile_changed_callbacks:
            try:
                callback(profile_name)
            except Exception as e:
                logger.exception("Error in profile changed callback: %s", e)

    def _emit_optimization_completed(self, results: dict[str, Any]) -> None:
        """Emit optimization completed event to all registered callbacks."""
        for callback in self.optimization_completed_callbacks:
            try:
                callback(results)
            except Exception as e:
                logger.exception("Error in optimization completed callback: %s", e)

    def _get_current_timestamp(self) -> str:
        """Get current timestamp for status."""
        return datetime.now().isoformat()

    def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate if available."""
        try:
            from src.core.cache_integration_service import cache_integration
            stats = cache_integration.get_cache_performance_stats()
            return stats.get("hit_rate_percent", 0.0)
        except ImportError:
            return 0.0

    def set_monitoring_enabled(self, enabled: bool) -> None:
        """Enable or disable performance monitoring."""
        self.monitoring_enabled = enabled
        logger.info("Performance monitoring %s", "enabled" if enabled else "disabled")

    def cleanup(self) -> None:
        """Clean up resources."""
        self.performance_warning_callbacks.clear()
        self.memory_pressure_callbacks.clear()
        self.profile_changed_callbacks.clear()
        self.optimization_completed_callbacks.clear()
        logger.info("Performance integration service cleaned up")


# Global performance integration service instance
performance_integration = PerformanceIntegrationService()


def get_performance_integration() -> PerformanceIntegrationService:
    """Get the global performance integration service."""
    return performance_integration