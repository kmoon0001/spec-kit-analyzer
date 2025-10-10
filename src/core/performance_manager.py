
"""Manages and monitors application performance metrics.

This module provides a centralized service for tracking system and process
performance, such as CPU and memory usage. It uses the `psutil` library
to gather real-time data, which can then be displayed in the GUI or used
for logging and diagnostics.
"""

import logging
import os
import platform
from dataclasses import dataclass
from enum import Enum
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class PerformanceProfile(Enum):
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"
    PERFORMANCE = "performance"


@dataclass
class PerformanceConfig:
    max_cache_memory_mb: int = 512
    batch_size: int = 4
    monitor_interval_seconds: int = 10


class PerformanceManager:
    """A singleton class to manage and provide performance metrics."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            instance = super().__new__(cls)
            instance.process = psutil.Process(os.getpid())
            instance.current_profile = PerformanceProfile.BALANCED
            instance.config = PerformanceConfig()
            instance.system_info = instance._gather_system_info()
            instance._cache_metrics = {"hits": 0, "misses": 0}
            cls._instance = instance
            logger.info("PerformanceManager initialized.")
        return cls._instance

    def _gather_system_info(self) -> dict[str, Any]:
        info: dict[str, Any] = {
            "cpu_count": psutil.cpu_count(logical=True) or 0,
            "platform": platform.platform(),
            "total_memory_gb": psutil.virtual_memory().total / (1024 ** 3),
        }
        try:
            import torch  # type: ignore

            info["cuda_available"] = bool(torch.cuda.is_available())
        except (ModuleNotFoundError, ImportError):
            info["cuda_available"] = False
        return info

    def set_profile(self, profile: PerformanceProfile | str) -> None:
        if isinstance(profile, str):
            try:
                profile = PerformanceProfile(profile.lower())
            except ValueError:
                logger.warning(
                    "Unknown performance profile '%s', keeping %s",
                    profile,
                    self.current_profile.value,
                )
                return
        self.current_profile = profile
        logger.info("Performance profile set to %s", profile.value)

    def record_cache_hit(self) -> None:
        self._cache_metrics["hits"] += 1

    def record_cache_miss(self) -> None:
        self._cache_metrics["misses"] += 1

    def cache_metrics(self) -> dict[str, int]:
        return dict(self._cache_metrics)

    def adaptive_cleanup(self) -> None:
        try:
            from .cache_service import cleanup_all_caches

            cleanup_all_caches()
            logger.info("Adaptive cleanup executed: caches cleared")
        except Exception as exc:
            logger.warning("Adaptive cleanup failed: %s", exc)

    def get_cpu_usage(self) -> float:
        try:
            return psutil.cpu_percent(interval=None)
        except Exception as exc:
            logger.exception("Could not retrieve CPU usage: %s", exc)
            return 0.0

    def get_memory_usage(self) -> dict[str, Any]:
        try:
            vmem = psutil.virtual_memory()
            process_mem_info = self.process.memory_info()
            return {
                "system_total_gb": vmem.total / (1024 ** 3),
                "system_available_gb": vmem.available / (1024 ** 3),
                "system_used_percent": vmem.percent,
                "process_rss_mb": process_mem_info.rss / (1024 ** 2),
                "process_memory_mb": process_mem_info.rss / (1024 ** 2),
            }
        except Exception as exc:
            logger.exception("Could not retrieve memory usage: %s", exc)
            return {}


# Global instance of the PerformanceManager
performance_manager = PerformanceManager()


def get_performance_manager() -> PerformanceManager:
    """Returns the global instance of the PerformanceManager."""
    return performance_manager
