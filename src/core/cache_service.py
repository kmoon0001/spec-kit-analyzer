"""
Intelligent caching service optimized for modest hardware (6-8GB RAM).
Implements memory-efficient LRU caching with automatic cleanup.
"""

import gc
import hashlib
import logging
import sys
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

import psutil

logger = logging.getLogger(__name__)


class MemoryAwareLRUCache:
    """
    Memory-aware LRU cache that automatically manages memory usage
    and adapts to system performance settings.
    """

    def __init__(self, max_memory_mb: Optional[int] = None):
        # Get max memory from performance manager if not specified
        if max_memory_mb is None:
            try:
                from .performance_manager import get_performance_config

                max_memory_mb = get_performance_config().max_cache_memory_mb
            except ImportError:
                max_memory_mb = 1024  # Fallback

        self.max_memory_mb = max_memory_mb
        self.cache: Dict[str, Dict] = {}
        self.access_times: Dict[str, datetime] = {}
        self.memory_usage = 0

    def _get_memory_usage_mb(self) -> float:
        """Get current system memory usage percentage."""
        return psutil.virtual_memory().percent

    def _get_cache_size_mb(self) -> float:
        """Estimate actual cache memory usage more accurately."""
        total_size = 0
        for key, data in self.cache.items():
            try:
                # More accurate size estimation using sys.getsizeof
                total_size += sys.getsizeof(data["data"])
                total_size += sys.getsizeof(key)
            except (TypeError, AttributeError):
                # Fallback to rough estimation
                total_size += 1024  # 1KB per entry as fallback

        return total_size / (1024 * 1024)  # Convert to MB

    def _cleanup_if_needed(self):
        """Clean up cache if memory usage is too high."""
        system_memory = self._get_memory_usage_mb()
        actual_cache_size = self._get_cache_size_mb()

        # Update our memory tracking with actual measurement
        self.memory_usage = actual_cache_size

        # If system memory > 80% or cache > max, cleanup oldest entries
        if system_memory > 80 or actual_cache_size > self.max_memory_mb:
            logger.info(
                "Memory cleanup triggered. System: %.1f%%, Cache: %.1f MB",
                system_memory,
                actual_cache_size,
            )

            # Remove oldest 25% of entries, but prioritize by type
            sorted_keys = sorted(
                self.access_times.keys(), key=lambda k: self.access_times[k]
            )

            cleanup_count = max(1, len(sorted_keys) // 4)

            # Prioritize removing large embeddings over small NER results
            embedding_keys = [k for k in sorted_keys if k.startswith("embedding_")]
            other_keys = [k for k in sorted_keys if not k.startswith("embedding_")]

            # Remove embeddings first (they're typically larger)
            keys_to_remove = (
                embedding_keys[: cleanup_count // 2] + other_keys[: cleanup_count // 2]
            )

            for key in keys_to_remove[:cleanup_count]:
                self._remove_entry(key)

            gc.collect()  # Force garbage collection
            logger.info("Cleaned up %d cache entries", len(keys_to_remove))

    def _remove_entry(self, key: str):
        """Remove a cache entry and update memory tracking."""
        if key in self.cache:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]

    def get(self, key: str) -> Optional[Any]:
        """Get cached value with memory awareness."""
        if key in self.cache:
            self.access_times[key] = datetime.now()
            return self.cache[key]["data"]
        return None

    def set(self, key: str, value: Any, ttl_hours: int = 24):
        """Set cached value with TTL and memory management."""
        self._cleanup_if_needed()

        # Don't cache if system memory is critically low
        if self._get_memory_usage_mb() > 90:
            logger.warning("System memory critical, skipping cache")
            return

        self.cache[key] = {
            "data": value,
            "expires": datetime.now() + timedelta(hours=ttl_hours),
        }
        self.access_times[key] = datetime.now()

    def clear_expired(self):
        """Remove expired entries."""
        now = datetime.now()
        expired_keys = [
            key for key, data in self.cache.items() if data["expires"] < now
        ]

        for key in expired_keys:
            self._remove_entry(key)


# Global cache instance
cache_service = MemoryAwareLRUCache()


class EmbeddingCache:
    """Specialized cache for document embeddings."""

    @staticmethod
    def _get_doc_hash(text: str) -> str:
        """Generate hash for document text."""
        return hashlib.md5(text.encode()).hexdigest()

    @staticmethod
    def get_embedding(text: str) -> Optional[List[float]]:
        """Get cached embedding for document text."""
        key = f"embedding_{EmbeddingCache._get_doc_hash(text)}"
        return cache_service.get(key)

    @staticmethod
    def set_embedding(text: str, embedding: List[float]):
        """Cache embedding for document text."""
        key = f"embedding_{EmbeddingCache._get_doc_hash(text)}"
        cache_service.set(key, embedding, ttl_hours=168)  # 1 week


class NERCache:
    """Specialized cache for NER results."""

    @staticmethod
    def get_ner_results(text: str, model_name: str) -> Optional[List[Dict]]:
        """Get cached NER results."""
        key = f"ner_{model_name}_{hashlib.md5(text.encode()).hexdigest()}"
        return cache_service.get(key)

    @staticmethod
    def set_ner_results(text: str, model_name: str, results: List[Dict]):
        """Cache NER results."""
        key = f"ner_{model_name}_{hashlib.md5(text.encode()).hexdigest()}"
        cache_service.set(key, results, ttl_hours=72)  # 3 days


class ComplianceRuleCache:
    """Cache for compliance rule retrievals."""

    @staticmethod
    @lru_cache(maxsize=500)  # Keep most common rules in memory
    def get_rules_for_discipline(discipline: str) -> List[Dict]:
        """Cached compliance rules by discipline."""
        # This would be implemented by the actual rule loading service
        return []

    @staticmethod
    def clear_rule_cache():
        """Clear the compliance rule cache."""
        ComplianceRuleCache.get_rules_for_discipline.cache_clear()


class DocumentCache:
    """Specialized cache for processed documents and their metadata."""

    @staticmethod
    def get_document_classification(doc_hash: str) -> Optional[Dict]:
        """Get cached document classification results."""
        key = f"doc_class_{doc_hash}"
        return cache_service.get(key)

    @staticmethod
    def set_document_classification(doc_hash: str, classification: Dict):
        """Cache document classification results."""
        key = f"doc_class_{doc_hash}"
        cache_service.set(key, classification, ttl_hours=168)  # 1 week

    @staticmethod
    def get_processed_chunks(doc_hash: str) -> Optional[List[str]]:
        """Get cached document chunks."""
        key = f"chunks_{doc_hash}"
        return cache_service.get(key)

    @staticmethod
    def set_processed_chunks(doc_hash: str, chunks: List[str]):
        """Cache processed document chunks."""
        key = f"chunks_{doc_hash}"
        cache_service.set(key, chunks, ttl_hours=72)  # 3 days


class LLMResponseCache:
    """Cache for LLM responses to avoid reprocessing identical queries."""

    @staticmethod
    def _get_query_hash(prompt: str, model_name: str) -> str:
        """Generate hash for LLM query."""
        combined = f"{model_name}:{prompt}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    @staticmethod
    def get_llm_response(prompt: str, model_name: str) -> Optional[str]:
        """Get cached LLM response."""
        key = f"llm_{LLMResponseCache._get_query_hash(prompt, model_name)}"
        return cache_service.get(key)

    @staticmethod
    def set_llm_response(prompt: str, model_name: str, response: str):
        """Cache LLM response."""
        key = f"llm_{LLMResponseCache._get_query_hash(prompt, model_name)}"
        # Shorter TTL for LLM responses as they may need updates
        cache_service.set(key, response, ttl_hours=24)  # 1 day


def get_cache_stats() -> Dict[str, Union[int, float]]:
    """Get comprehensive cache statistics for monitoring."""
    return {
        "total_entries": len(cache_service.cache),
        "memory_usage_mb": cache_service._get_cache_size_mb(),
        "system_memory_percent": cache_service._get_memory_usage_mb(),
        "embedding_entries": len(
            [k for k in cache_service.cache.keys() if k.startswith("embedding_")]
        ),
        "ner_entries": len(
            [k for k in cache_service.cache.keys() if k.startswith("ner_")]
        ),
        "llm_entries": len(
            [k for k in cache_service.cache.keys() if k.startswith("llm_")]
        ),
        "doc_entries": len(
            [
                k
                for k in cache_service.cache.keys()
                if k.startswith("doc_") or k.startswith("chunks_")
            ]
        ),
    }


def cleanup_all_caches():
    """Cleanup all caches - call periodically or on low memory."""
    stats_before = get_cache_stats()

    cache_service.clear_expired()
    cache_service._cleanup_if_needed()
    ComplianceRuleCache.clear_rule_cache()
    gc.collect()

    stats_after = get_cache_stats()
    logger.info(
        "Cache cleanup completed. Entries: %d -> %d, Memory: %.1f MB -> %.1f MB",
        stats_before["total_entries"],
        stats_after["total_entries"],
        stats_before["memory_usage_mb"],
        stats_after["memory_usage_mb"],
    )


def warm_cache_on_startup():
    """Pre-populate cache with commonly used data on application startup."""
    logger.info("Warming up cache with common compliance rules...")
    # This would be called during app initialization to load frequently used rules
    # Implementation would depend on the actual rubric loading service
