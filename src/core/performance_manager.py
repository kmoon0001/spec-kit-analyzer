"""
Manages and monitors application performance metrics.

This module provides a centralized service for tracking system and process
performance, such as CPU and memory usage. It uses the `psutil` library
to gather real-time data, which can then be displayed in the GUI or used
for logging and diagnostics.
"""

import logging
import psutil
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PerformanceManager:
    """A singleton class to manage and provide performance metrics."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PerformanceManager, cls).__new__(cls)
            cls._instance.process = psutil.Process(os.getpid())
            logger.info("PerformanceManager initialized.")
        return cls._instance

    def get_cpu_usage(self) -> float:
        """Returns the current system-wide CPU utilization as a percentage."""
        try:
            return psutil.cpu_percent(interval=None)
        except Exception as e:
            logger.error(f"Could not retrieve CPU usage: {e}")
            return 0.0

    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Returns a dictionary of memory usage statistics, including system-wide
        and process-specific memory usage.
        """
        try:
            vmem = psutil.virtual_memory()
            process_mem_info = self.process.memory_info()
            return {
                "system_total_gb": vmem.total / (1024**3),
                "system_available_gb": vmem.available / (1024**3),
                "system_used_percent": vmem.percent,
                "process_rss_mb": process_mem_info.rss / (1024**2), # Resident Set Size
            }
        except Exception as e:
            logger.error(f"Could not retrieve memory usage: {e}")
            return {}

# Global instance of the PerformanceManager
performance_manager = PerformanceManager()

def get_performance_manager() -> PerformanceManager:
    """Returns the global instance of the PerformanceManager."""
    return performance_manager
