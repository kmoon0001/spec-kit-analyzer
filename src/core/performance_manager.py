"""
Adaptive Performance Manager for Therapy Compliance Analyzer
Automatically detects system capabilities and adjusts performance settings.
"""

import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

import psutil

logger = logging.getLogger(__name__)


class PerformanceProfile(Enum):
    """Performance profiles based on system capabilities."""

    CONSERVATIVE = "conservative"  # 6-8GB RAM, integrated graphics
    BALANCED = "balanced"  # 8-12GB RAM, dedicated GPU optional
    AGGRESSIVE = "aggressive"  # 12-16GB+ RAM, dedicated GPU
    CUSTOM = "custom"  # User-defined settings


@dataclass
class PerformanceConfig:
    """Configuration for performance optimization settings."""

    # Memory Management
    max_cache_memory_mb: int
    embedding_cache_size: int
    ner_cache_size: int

    # AI/ML Settings
    use_gpu: bool
    model_quantization: bool
    batch_size: int
    max_sequence_length: int

    # Database Settings
    connection_pool_size: int
    async_operations: bool

    # Processing Settings
    chunk_size: int
    parallel_processing: bool
    max_workers: int


class SystemProfiler:
    """Analyzes system capabilities and recommends performance settings."""

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get comprehensive system information."""
        import torch

        memory = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()

        # Check for CUDA availability
        cuda_available = torch.cuda.is_available()
        gpu_memory = 0
        gpu_name = "None"

        if cuda_available:
            try:
                gpu_memory = torch.cuda.get_device_properties(0).total_memory // (
                    1024**3
                )  # GB
                gpu_name = torch.cuda.get_device_name(0)
            except Exception as e:
                logger.warning("Could not get GPU info: %s", e)
                cuda_available = False

        return {
            "total_memory_gb": memory.total // (1024**3),
            "available_memory_gb": memory.available // (1024**3),
            "cpu_count": cpu_count,
            "cuda_available": cuda_available,
            "gpu_memory_gb": gpu_memory,
            "gpu_name": gpu_name,
        }

    @staticmethod
    def recommend_profile(system_info: Dict[str, Any]) -> PerformanceProfile:
        """Recommend performance profile based on system capabilities."""
        memory_gb = system_info["total_memory_gb"]
        has_gpu = system_info["cuda_available"]

        if memory_gb >= 16 and has_gpu:
            return PerformanceProfile.AGGRESSIVE
        if memory_gb >= 12 or (memory_gb >= 8 and has_gpu):
            return PerformanceProfile.BALANCED
        return PerformanceProfile.CONSERVATIVE


class PerformanceManager:
    """Manages performance settings and system resource utilization."""

    def __init__(self, config_path: str = "performance_config.json"):
        self.config_path = config_path
        self.system_info = SystemProfiler.get_system_info()
        self.current_profile = PerformanceProfile.BALANCED
        self.config = self._load_or_create_config()

        # Save config after initialization is complete
        try:
            self.save_config()
        except Exception as e:
            logger.warning(f"Could not save initial config: {e}")

        logger.info("System detected: %s", self.system_info)
        logger.info("Performance profile: %s", self.current_profile.value)

    def _load_or_create_config(self) -> PerformanceConfig:
        """
        Load existing config or create a new one. This version is hardened
        against empty or corrupted config files.
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if not content:
                        logger.warning(
                            "Performance config file is empty. A new one will be created."
                        )
                    else:
                        data = json.loads(content)
                        self.current_profile = PerformanceProfile(
                            data.get("profile", "balanced")
                        )
                        # Note: This logic re-creates the config based on the profile,
                        # ignoring other custom values. For this fix, we are preserving
                        # this behavior to minimize changes, focusing on stability.
                        logger.info(
                            "Loaded performance profile: %s", self.current_profile.value
                        )
                        return self._create_config_for_profile(self.current_profile)
            except json.JSONDecodeError as e:
                logger.warning(
                    "Could not parse performance_config.json: %s. A new configuration will be created.",
                    e,
                )
            except Exception as e:
                logger.error(
                    "An unexpected error occurred loading performance config: %s. Creating a new one.",
                    e,
                    exc_info=True,
                )

        # Auto-detect and create new config if loading fails or file doesn't exist
        logger.info("Creating a new performance configuration based on system profile.")
        recommended_profile = SystemProfiler.recommend_profile(self.system_info)
        self.current_profile = recommended_profile
        return self._create_config_for_profile(recommended_profile)

    def _create_config_for_profile(
        self, profile: PerformanceProfile
    ) -> PerformanceConfig:
        """Create performance config for specific profile."""
        memory_gb = self.system_info["total_memory_gb"]
        has_gpu = self.system_info["cuda_available"]
        cpu_count = self.system_info["cpu_count"]

        if profile == PerformanceProfile.CONSERVATIVE:
            return PerformanceConfig(
                max_cache_memory_mb=1024,  # 1GB cache
                embedding_cache_size=500,
                ner_cache_size=200,
                use_gpu=False,  # Conservative: CPU only
                model_quantization=True,  # Use quantized models
                batch_size=1,
                max_sequence_length=512,
                connection_pool_size=5,
                async_operations=False,  # Simpler synchronous operations
                chunk_size=1000,
                parallel_processing=False,
                max_workers=2,
            )

        elif profile == PerformanceProfile.BALANCED:
            return PerformanceConfig(
                max_cache_memory_mb=min(
                    2048, memory_gb * 200
                ),  # Up to 2GB or 20% of RAM
                embedding_cache_size=1000,
                ner_cache_size=500,
                use_gpu=has_gpu,  # Use GPU if available
                model_quantization=True,
                batch_size=2 if has_gpu else 1,
                max_sequence_length=1024,
                connection_pool_size=10,
                async_operations=True,
                chunk_size=2000,
                parallel_processing=True,
                max_workers=min(4, cpu_count),
            )

        elif profile == PerformanceProfile.AGGRESSIVE:
            return PerformanceConfig(
                max_cache_memory_mb=min(
                    4096, memory_gb * 300
                ),  # Up to 4GB or 30% of RAM
                embedding_cache_size=2000,
                ner_cache_size=1000,
                use_gpu=has_gpu,
                model_quantization=False,  # Full precision models
                batch_size=4 if has_gpu else 2,
                max_sequence_length=2048,
                connection_pool_size=20,
                async_operations=True,
                chunk_size=4000,
                parallel_processing=True,
                max_workers=min(8, cpu_count),
            )

        else:  # CUSTOM - use balanced as default
            return self._create_config_for_profile(PerformanceProfile.BALANCED)

    def save_config(self):
        """Save current configuration to file."""
        config_data = {
            "profile": self.current_profile.value,
            "system_info": self.system_info,
            "config": {
                "max_cache_memory_mb": self.config.max_cache_memory_mb,
                "embedding_cache_size": self.config.embedding_cache_size,
                "ner_cache_size": self.config.ner_cache_size,
                "use_gpu": self.config.use_gpu,
                "model_quantization": self.config.model_quantization,
                "batch_size": self.config.batch_size,
                "max_sequence_length": self.config.max_sequence_length,
                "connection_pool_size": self.config.connection_pool_size,
                "async_operations": self.config.async_operations,
                "chunk_size": self.config.chunk_size,
                "parallel_processing": self.config.parallel_processing,
                "max_workers": self.config.max_workers,
            },
        }

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)
            logger.info("Performance config saved to %s", self.config_path)
        except Exception as e:
            logger.error("Could not save config: %s", e)

    def set_profile(self, profile: PerformanceProfile):
        """Change performance profile and update configuration."""
        self.current_profile = profile
        self.config = self._create_config_for_profile(profile)
        self.save_config()
        logger.info("Performance profile changed to: %s", profile.value)

    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics."""
        memory = psutil.virtual_memory()
        process = psutil.Process()

        return {
            "system_total_gb": memory.total / (1024**3),
            "system_used_percent": memory.percent,
            "system_available_gb": memory.available / (1024**3),
            "process_memory_mb": process.memory_info().rss / (1024**2),
            "cache_limit_mb": self.config.max_cache_memory_mb,
        }

    def should_use_gpu(self) -> bool:
        """Check if GPU should be used based on current config and availability."""
        import torch

        return self.config.use_gpu and torch.cuda.is_available()

    def get_optimal_batch_size(self, base_size: Optional[int] = None) -> int:
        """Get optimal batch size based on current memory usage."""
        if base_size is None:
            base_size = self.config.batch_size

        memory_usage = self.get_memory_usage()

        # Reduce batch size if memory usage is high
        if memory_usage["system_used_percent"] > 85:
            return max(1, base_size // 2)
        if memory_usage["system_used_percent"] > 70:
            return max(1, int(base_size * 0.75))

        return base_size

    def adaptive_cleanup(self):
        """Perform adaptive cleanup based on memory pressure."""
        memory_usage = self.get_memory_usage()

        if memory_usage["system_used_percent"] > 80:
            logger.info("High memory usage detected, performing cleanup")
            # Import here to avoid circular imports
            from .cache_service import cleanup_all_caches

            cleanup_all_caches()

            # Force garbage collection
            import gc

            gc.collect()


# Global performance manager instance
performance_manager = PerformanceManager()


def get_performance_config() -> PerformanceConfig:
    """Get current performance configuration."""
    return performance_manager.config


def get_system_info() -> Dict[str, Any]:
    """Get system information."""
    return performance_manager.system_info