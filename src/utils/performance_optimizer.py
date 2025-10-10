"""
Performance optimization utilities for the Therapy Compliance Analyzer.

This module provides automatic performance tuning based on system capabilities
and runtime performance monitoring.
"""

import json
import logging
import os
import platform
from typing import Any

import psutil  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """Automatically optimize configuration based on system capabilities."""

    def __init__(self):
        self.system_info = self._get_system_info()
        self.performance_profile = self._determine_performance_profile()

    def _get_system_info(self) -> dict[str, Any]:
        """Gather system information for optimization."""
        try:
            # Memory information
            memory = psutil.virtual_memory()
            total_memory_gb = memory.total / (1024**3)
            available_memory_gb = memory.available / (1024**3)

            # CPU information
            cpu_count = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()

            # GPU information (basic check)
            gpu_available = False
            gpu_memory_gb = 0
            gpu_name = "None"

            try:
                import torch

                if torch.cuda.is_available():
                    gpu_available = True
                    gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (
                        1024**3
                    )
                    gpu_name = torch.cuda.get_device_name(0)
            except ImportError:
                pass

            return {
                "total_memory_gb": round(total_memory_gb, 1),
                "available_memory_gb": round(available_memory_gb, 1),
                "cpu_count": cpu_count,
                "cpu_freq_mhz": cpu_freq.current if cpu_freq else 0,
                "platform": platform.system(),
                "architecture": platform.architecture()[0],
                "cuda_available": gpu_available,
                "gpu_memory_gb": round(gpu_memory_gb, 1),
                "gpu_name": gpu_name,
            }
        except Exception as e:
            logger.warning(f"Failed to gather system info: {e}")
            return {
                "total_memory_gb": 8.0,  # Conservative default
                "available_memory_gb": 4.0,
                "cpu_count": 4,
                "cpu_freq_mhz": 2000,
                "platform": "Unknown",
                "architecture": "64bit",
                "cuda_available": False,
                "gpu_memory_gb": 0,
                "gpu_name": "None",
            }

    def _determine_performance_profile(self) -> str:
        """Determine the appropriate performance profile based on system capabilities."""
        memory_gb = self.system_info["total_memory_gb"]
        cpu_count = self.system_info["cpu_count"]

        if memory_gb >= 16 and cpu_count >= 8:
            return "high_performance"
        elif memory_gb >= 8 and cpu_count >= 4:
            return "balanced"
        else:
            return "conservative"

    def get_optimized_config(self) -> dict[str, Any]:
        """Generate optimized configuration based on system capabilities."""
        base_config = {
            "profile": self.performance_profile,
            "system_info": self.system_info,
        }

        if self.performance_profile == "high_performance":
            config = {
                "max_cache_memory_mb": 4096,
                "embedding_cache_size": 2000,
                "ner_cache_size": 1000,
                "llm_cache_size": 500,
                "use_gpu": self.system_info["cuda_available"],
                "model_quantization": False,  # Use full precision if memory allows
                "batch_size": 8,
                "max_sequence_length": 1024,
                "connection_pool_size": 10,
                "async_operations": True,
                "chunk_size": 2000,
                "parallel_processing": True,
                "max_workers": min(self.system_info["cpu_count"], 8),
            }
        elif self.performance_profile == "balanced":
            config = {
                "max_cache_memory_mb": 2048,
                "embedding_cache_size": 1000,
                "ner_cache_size": 500,
                "llm_cache_size": 200,
                "use_gpu": self.system_info["cuda_available"],
                "model_quantization": True,
                "batch_size": 4,
                "max_sequence_length": 512,
                "connection_pool_size": 5,
                "async_operations": True,
                "chunk_size": 1000,
                "parallel_processing": True,
                "max_workers": min(self.system_info["cpu_count"], 4),
            }
        else:  # conservative
            config = {
                "max_cache_memory_mb": 1024,
                "embedding_cache_size": 500,
                "ner_cache_size": 200,
                "llm_cache_size": 100,
                "use_gpu": False,  # Disable GPU for conservative profile
                "model_quantization": True,
                "batch_size": 1,
                "max_sequence_length": 256,
                "connection_pool_size": 3,
                "async_operations": False,
                "chunk_size": 500,
                "parallel_processing": False,
                "max_workers": 1,
            }

        base_config["config"] = config
        return base_config

    def save_performance_config(self, filepath: str | None = None) -> str:
        """Save the optimized performance configuration to a file."""
        if filepath is None:
            filepath = "performance_config.json"

        config = self.get_optimized_config()

        try:
            with open(filepath, "w") as f:
                json.dump(config, f, indent=2)
            logger.info(f"Performance configuration saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save performance config: {e}")
            raise

    def load_performance_config(self, filepath: str | None = None) -> dict[str, Any]:
        """Load performance configuration from file."""
        if filepath is None:
            filepath = "performance_config.json"

        if not os.path.exists(filepath):
            logger.info("No existing performance config found, generating new one")
            return self.get_optimized_config()

        try:
            with open(filepath) as f:
                config = json.load(f)
            logger.info(f"Performance configuration loaded from {filepath}")
            return config
        except Exception as e:
            logger.warning(f"Failed to load performance config: {e}, using defaults")
            return self.get_optimized_config()

    def monitor_performance(self) -> dict[str, Any]:
        """Monitor current system performance metrics."""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Disk usage for temp directory
            disk_usage = psutil.disk_usage(".")
            disk_percent = (disk_usage.used / disk_usage.total) * 100

            return {
                "memory_usage_percent": memory_percent,
                "cpu_usage_percent": cpu_percent,
                "disk_usage_percent": round(disk_percent, 1),
                "available_memory_gb": round(memory.available / (1024**3), 1),
                "timestamp": psutil.boot_time(),
            }
        except Exception as e:
            logger.warning(f"Failed to monitor performance: {e}")
            return {}

    def should_adjust_performance(self, current_metrics: dict[str, Any]) -> bool:
        """Determine if performance settings should be adjusted based on current metrics."""
        memory_usage = current_metrics.get("memory_usage_percent", 0)
        cpu_usage = current_metrics.get("cpu_usage_percent", 0)

        # Adjust if memory usage is consistently high
        if memory_usage > 85:
            logger.warning(f"High memory usage detected: {memory_usage}%")
            return True

        # Adjust if CPU usage is consistently high
        if cpu_usage > 90:
            logger.warning(f"High CPU usage detected: {cpu_usage}%")
            return True

        return False

    def get_model_recommendations(self) -> dict[str, Any]:
        """Get model recommendations based on system capabilities."""
        memory_gb = self.system_info["total_memory_gb"]

        if memory_gb >= 16:
            return {
                "generator_profile": "enhanced",
                "quantization": "fp16",
                "context_length": 4096,
                "recommendation": "High-end models with full precision",
            }
        elif memory_gb >= 8:
            return {
                "generator_profile": "standard",
                "quantization": "q4_k_m",
                "context_length": 2048,
                "recommendation": "Balanced models with 4-bit quantization",
            }
        else:
            return {
                "generator_profile": "lightweight",
                "quantization": "q4_0",
                "context_length": 1024,
                "recommendation": "Lightweight models with aggressive quantization",
            }


def optimize_system_performance() -> dict[str, Any]:
    """Main function to optimize system performance configuration."""
    optimizer = PerformanceOptimizer()

    # Generate and save optimized configuration
    config = optimizer.get_optimized_config()
    optimizer.save_performance_config()

    # Get model recommendations
    model_recommendations = optimizer.get_model_recommendations()
    config["model_recommendations"] = model_recommendations

    # Log optimization results
    logger.info(f"System optimized for {config['profile']} performance profile")
    logger.info(
        f"System specs: {config['system_info']['total_memory_gb']}GB RAM, "
        f"{config['system_info']['cpu_count']} CPUs"
    )

    return config


if __name__ == "__main__":
    # Run optimization when script is executed directly
    logging.basicConfig(level=logging.INFO)
    result = optimize_system_performance()
    logger.info(f"Performance optimization complete. Profile: {result['profile']}")
