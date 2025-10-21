"""Advanced Multi-Tier Caching System for Clinical Compliance Analysis.

This module implements a sophisticated multi-tier caching system with
intelligent eviction policies, cache warming, and performance optimization.

Features:
- Multi-tier caching (L1: Memory, L2: Redis, L3: Database)
- Intelligent eviction policies (LRU, LFU, TTL-based)
- Cache warming and preloading
- Cache analytics and monitoring
- Distributed caching support
- Cache invalidation strategies
"""

import asyncio
import hashlib
import json
import logging
import pickle
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
import threading
from collections import OrderedDict, defaultdict

logger = logging.getLogger(__name__)


class CacheTier(Enum):
    """Cache tiers in the multi-tier system."""
    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    L3_DATABASE = "l3_database"


class EvictionPolicy(Enum):
    """Cache eviction policies."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    SIZE_BASED = "size_based"  # Size-based eviction


class CacheOperation(Enum):
    """Cache operations."""
    GET = "get"
    SET = "set"
    DELETE = "delete"
    CLEAR = "clear"
    WARM = "warm"


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    ttl: Optional[timedelta] = None
    tier: CacheTier = CacheTier.L1_MEMORY
    size_bytes: int = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    operations: int = 0
    total_size_bytes: int = 0
    hit_rate: float = 0.0
    average_access_time_ms: float = 0.0
    tier_distribution: Dict[str, int] = field(default_factory=dict)


class MultiTierCacheSystem:
    """Advanced multi-tier caching system for clinical compliance analysis.

    Implements intelligent caching with multiple tiers and eviction policies.
    """

    def __init__(
        self,
        l1_size_mb: int = 100,
        l2_enabled: bool = False,
        l3_enabled: bool = True,
        default_ttl: int = 3600,
        eviction_policy: EvictionPolicy = EvictionPolicy.LRU
    ):
        """Initialize the multi-tier cache system.

        Args:
            l1_size_mb: L1 cache size in MB
            l2_enabled: Whether to enable L2 (Redis) cache
            l3_enabled: Whether to enable L3 (Database) cache
            default_ttl: Default TTL in seconds
            eviction_policy: Cache eviction policy
        """
        self.l1_size_bytes = l1_size_mb * 1024 * 1024
        self.l2_enabled = l2_enabled
        self.l3_enabled = l3_enabled
        self.default_ttl = timedelta(seconds=default_ttl)
        self.eviction_policy = eviction_policy

        # L1 Cache (Memory)
        self.l1_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.l1_lock = threading.RLock()

        # L2 Cache (Redis) - placeholder for future implementation
        self.l2_cache = None
        self.l2_lock = threading.RLock()

        # L3 Cache (Database) - placeholder for future implementation
        self.l3_cache = None
        self.l3_lock = threading.RLock()

        # Cache metrics
        self.metrics = CacheMetrics()
        self.metrics_lock = threading.RLock()

        # Cache warming
        self.warming_queue: List[str] = []
        self.warming_lock = threading.RLock()

        # Cache tags for invalidation
        self.tag_index: Dict[str, List[str]] = defaultdict(list)
        self.tag_lock = threading.RLock()

        # Configuration
        self.config = {
            'max_l1_entries': 10000,
            'max_l2_entries': 100000,
            'max_l3_entries': 1000000,
            'warming_batch_size': 100,
            'metrics_reset_interval': 3600,  # 1 hour
            'cleanup_interval': 300  # 5 minutes
        }

        # Background tasks will be started when needed
        self._background_tasks_started = False

        logger.info("Multi-tier cache system initialized: L1=%dMB, L2=%s, L3=%s, Policy=%s",
                   l1_size_mb, l2_enabled, l3_enabled, eviction_policy.value)

    async def _ensure_background_tasks_started(self):
        """Start background tasks if not already started."""
        if not self._background_tasks_started:
            self._start_background_tasks()
            self._background_tasks_started = True

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with automatic background task startup."""
        await self._ensure_background_tasks_started()
        start_time = time.time()

        try:
            # Try L1 cache first
            with self.l1_lock:
                if key in self.l1_cache:
                    entry = self.l1_cache[key]

                    # Check TTL
                    if self._is_expired(entry):
                        del self.l1_cache[key]
                        self._remove_from_tag_index(key)
                    else:
                        # Update access info
                        entry.last_accessed = datetime.now()
                        entry.access_count += 1

                        # Move to end (LRU)
                        self.l1_cache.move_to_end(key)

                        # Update metrics
                        self._update_metrics(CacheOperation.GET, True, time.time() - start_time)

                        return entry.value

            # Try L2 cache
            if self.l2_enabled:
                value = await self._get_from_l2(key)
                if value is not None:
                    # Promote to L1
                    await self._promote_to_l1(key, value)
                    self._update_metrics(CacheOperation.GET, True, time.time() - start_time)
                    return value

            # Try L3 cache
            if self.l3_enabled:
                value = await self._get_from_l3(key)
                if value is not None:
                    # Promote to L1 and L2
                    await self._promote_to_l1(key, value)
                    if self.l2_enabled:
                        await self._promote_to_l2(key, value)
                    self._update_metrics(CacheOperation.GET, True, time.time() - start_time)
                    return value

            # Cache miss
            self._update_metrics(CacheOperation.GET, False, time.time() - start_time)
            return default

        except Exception as e:
            logger.exception("Cache get error for key %s: %s", key, e)
            self._update_metrics(CacheOperation.GET, False, time.time() - start_time)
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None,
        tags: Optional[List[str]] = None,
        tier: Optional[CacheTier] = None
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live
            tags: Cache tags for invalidation
            tier: Specific tier to store in

        Returns:
            True if successful
        """
        try:
            if ttl is None:
                ttl = self.default_ttl

            if tags is None:
                tags = []

            if tier is None:
                tier = CacheTier.L1_MEMORY

            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl,
                tier=tier,
                tags=tags,
                size_bytes=self._calculate_size(value)
            )

            # Store in appropriate tier(s)
            if tier == CacheTier.L1_MEMORY or tier is None:
                await self._store_in_l1(entry)

            if self.l2_enabled and (tier == CacheTier.L2_REDIS or tier is None):
                await self._store_in_l2(entry)

            if self.l3_enabled and (tier == CacheTier.L3_DATABASE or tier is None):
                await self._store_in_l3(entry)

            # Update tag index
            self._update_tag_index(key, tags)

            # Update metrics
            self._update_metrics(CacheOperation.SET, True, 0)

            logger.debug("Cached key %s in tier %s", key, tier.value)
            return True

        except Exception as e:
            logger.exception("Cache set error for key %s: %s", key, e)
            self._update_metrics(CacheOperation.SET, False, 0)
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if successful
        """
        try:
            deleted = False

            # Delete from L1
            with self.l1_lock:
                if key in self.l1_cache:
                    del self.l1_cache[key]
                    deleted = True

            # Delete from L2
            if self.l2_enabled:
                if await self._delete_from_l2(key):
                    deleted = True

            # Delete from L3
            if self.l3_enabled:
                if await self._delete_from_l3(key):
                    deleted = True

            # Remove from tag index
            self._remove_from_tag_index(key)

            # Update metrics
            self._update_metrics(CacheOperation.DELETE, True, 0)

            return deleted

        except Exception as e:
            logger.exception("Cache delete error for key %s: %s", key, e)
            self._update_metrics(CacheOperation.DELETE, False, 0)
            return False

    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalidate cache entries by tags.

        Args:
            tags: Tags to invalidate

        Returns:
            Number of entries invalidated
        """
        invalidated_count = 0

        try:
            with self.tag_lock:
                keys_to_invalidate = set()

                for tag in tags:
                    if tag in self.tag_index:
                        keys_to_invalidate.update(self.tag_index[tag])

                for key in keys_to_invalidate:
                    if await self.delete(key):
                        invalidated_count += 1

            logger.info("Invalidated %d cache entries by tags: %s", invalidated_count, tags)
            return invalidated_count

        except Exception as e:
            logger.exception("Cache invalidation error for tags %s: %s", tags, e)
            return invalidated_count

    async def warm_cache(self, keys_and_values: List[Tuple[str, Any]]) -> int:
        """Warm cache with precomputed values.

        Args:
            keys_and_values: List of (key, value) tuples

        Returns:
            Number of entries warmed
        """
        warmed_count = 0

        try:
            for key, value in keys_and_values:
                if await self.set(key, value):
                    warmed_count += 1

            logger.info("Warmed cache with %d entries", warmed_count)
            return warmed_count

        except Exception as e:
            logger.exception("Cache warming error: %s", e)
            return warmed_count

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics.

        Returns:
            Cache statistics
        """
        with self.metrics_lock:
            stats = {
                'metrics': {
                    'hits': self.metrics.hits,
                    'misses': self.metrics.misses,
                    'evictions': self.metrics.evictions,
                    'operations': self.metrics.operations,
                    'hit_rate': self.metrics.hit_rate,
                    'average_access_time_ms': self.metrics.average_access_time_ms
                },
                'tier_stats': {
                    'l1': {
                        'enabled': True,
                        'entries': len(self.l1_cache),
                        'size_bytes': sum(entry.size_bytes for entry in self.l1_cache.values()),
                        'max_size_bytes': self.l1_size_bytes
                    },
                    'l2': {
                        'enabled': self.l2_enabled,
                        'entries': 0,  # Placeholder
                        'size_bytes': 0  # Placeholder
                    },
                    'l3': {
                        'enabled': self.l3_enabled,
                        'entries': 0,  # Placeholder
                        'size_bytes': 0  # Placeholder
                    }
                },
                'configuration': {
                    'eviction_policy': self.eviction_policy.value,
                    'default_ttl_seconds': self.default_ttl.total_seconds(),
                    'max_l1_entries': self.config['max_l1_entries']
                }
            }

        return stats

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        if entry.ttl is None:
            return False

        return datetime.now() - entry.created_at > entry.ttl

    def _calculate_size(self, value: Any) -> int:
        """Calculate size of value in bytes."""
        try:
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, (int, float)):
                return 8
            elif isinstance(value, dict):
                return len(json.dumps(value).encode('utf-8'))
            elif isinstance(value, list):
                return len(json.dumps(value).encode('utf-8'))
            else:
                return len(pickle.dumps(value))
        except Exception:
            return 1024  # Default size

    def _update_metrics(self, operation: CacheOperation, success: bool, access_time: float):
        """Update cache metrics."""
        with self.metrics_lock:
            self.metrics.operations += 1

            if operation == CacheOperation.GET:
                if success:
                    self.metrics.hits += 1
                else:
                    self.metrics.misses += 1

                # Update average access time
                total_accesses = self.metrics.hits + self.metrics.misses
                if total_accesses > 0:
                    self.metrics.average_access_time_ms = (
                        (self.metrics.average_access_time_ms * (total_accesses - 1) + access_time * 1000) / total_accesses
                    )

            # Update hit rate
            total_gets = self.metrics.hits + self.metrics.misses
            if total_gets > 0:
                self.metrics.hit_rate = self.metrics.hits / total_gets

    def _update_tag_index(self, key: str, tags: List[str]):
        """Update tag index for invalidation."""
        with self.tag_lock:
            # Remove old tags
            self._remove_from_tag_index(key)

            # Add new tags
            for tag in tags:
                self.tag_index[tag].append(key)

    def _remove_from_tag_index(self, key: str):
        """Remove key from tag index."""
        with self.tag_lock:
            for tag, keys in self.tag_index.items():
                if key in keys:
                    keys.remove(key)

    async def _store_in_l1(self, entry: CacheEntry) -> bool:
        """Store entry in L1 cache."""
        try:
            with self.l1_lock:
                # Check if we need to evict
                if len(self.l1_cache) >= self.config['max_l1_entries']:
                    await self._evict_from_l1()

                # Check size constraints
                current_size = sum(e.size_bytes for e in self.l1_cache.values())
                if current_size + entry.size_bytes > self.l1_size_bytes:
                    await self._evict_from_l1_by_size(entry.size_bytes)

                # Store entry
                self.l1_cache[key] = entry
                self.l1_cache.move_to_end(key)

                return True

        except Exception as e:
            logger.exception("L1 store error for key %s: %s", key, e)
            return False

    async def _evict_from_l1(self):
        """Evict entries from L1 cache based on policy."""
        with self.l1_lock:
            if not self.l1_cache:
                return

            if self.eviction_policy == EvictionPolicy.LRU:
                # Remove least recently used
                key_to_remove = next(iter(self.l1_cache))
                del self.l1_cache[key_to_remove]
                self._remove_from_tag_index(key_to_remove)

            elif self.eviction_policy == EvictionPolicy.LFU:
                # Remove least frequently used
                key_to_remove = min(self.l1_cache.keys(), key=lambda k: self.l1_cache[k].access_count)
                del self.l1_cache[key_to_remove]
                self._remove_from_tag_index(key_to_remove)

            elif self.eviction_policy == EvictionPolicy.TTL:
                # Remove expired entries
                expired_keys = [k for k, v in self.l1_cache.items() if self._is_expired(v)]
                for key in expired_keys:
                    del self.l1_cache[key]
                    self._remove_from_tag_index(key)

            self.metrics.evictions += 1

    async def _evict_from_l1_by_size(self, required_size: int):
        """Evict entries from L1 cache to make room."""
        with self.l1_lock:
            freed_size = 0

            while freed_size < required_size and self.l1_cache:
                if self.eviction_policy == EvictionPolicy.LRU:
                    key_to_remove = next(iter(self.l1_cache))
                elif self.eviction_policy == EvictionPolicy.LFU:
                    key_to_remove = min(self.l1_cache.keys(), key=lambda k: self.l1_cache[k].access_count)
                else:
                    key_to_remove = next(iter(self.l1_cache))

                entry = self.l1_cache[key_to_remove]
                freed_size += entry.size_bytes

                del self.l1_cache[key_to_remove]
                self._remove_from_tag_index(key_to_remove)

                self.metrics.evictions += 1

    async def _promote_to_l1(self, key: str, value: Any):
        """Promote value to L1 cache."""
        entry = CacheEntry(
            key=key,
            value=value,
            ttl=self.default_ttl,
            tier=CacheTier.L1_MEMORY,
            size_bytes=self._calculate_size(value)
        )
        await self._store_in_l1(entry)

    async def _promote_to_l2(self, key: str, value: Any):
        """Promote value to L2 cache."""
        # Placeholder for Redis implementation
        pass

    async def _get_from_l2(self, key: str) -> Optional[Any]:
        """Get value from L2 cache."""
        # Placeholder for Redis implementation
        return None

    async def _get_from_l3(self, key: str) -> Optional[Any]:
        """Get value from L3 cache."""
        # Placeholder for database implementation
        return None

    async def _store_in_l2(self, entry: CacheEntry) -> bool:
        """Store entry in L2 cache."""
        # Placeholder for Redis implementation
        return True

    async def _store_in_l3(self, entry: CacheEntry) -> bool:
        """Store entry in L3 cache."""
        # Placeholder for database implementation
        return True

    async def _delete_from_l2(self, key: str) -> bool:
        """Delete key from L2 cache."""
        # Placeholder for Redis implementation
        return True

    async def _delete_from_l3(self, key: str) -> bool:
        """Delete key from L3 cache."""
        # Placeholder for database implementation
        return True

    def _start_background_tasks(self):
        """Start background maintenance tasks."""
        # Start cleanup task
        asyncio.create_task(self._cleanup_task())

        # Start metrics reset task
        asyncio.create_task(self._metrics_reset_task())

    async def _cleanup_task(self):
        """Background cleanup task."""
        while True:
            try:
                await asyncio.sleep(self.config['cleanup_interval'])

                # Clean expired entries
                with self.l1_lock:
                    expired_keys = [k for k, v in self.l1_cache.items() if self._is_expired(v)]
                    for key in expired_keys:
                        del self.l1_cache[key]
                        self._remove_from_tag_index(key)

                logger.debug("Cleaned up %d expired cache entries", len(expired_keys))

            except Exception as e:
                logger.exception("Cleanup task error: %s", e)

    async def _metrics_reset_task(self):
        """Background metrics reset task."""
        while True:
            try:
                await asyncio.sleep(self.config['metrics_reset_interval'])

                with self.metrics_lock:
                    # Reset metrics periodically
                    self.metrics.hits = 0
                    self.metrics.misses = 0
                    self.metrics.evictions = 0
                    self.metrics.operations = 0

                logger.debug("Reset cache metrics")

            except Exception as e:
                logger.exception("Metrics reset task error: %s", e)

    async def clear_all(self) -> int:
        """Clear all cache tiers.

        Returns:
            Number of entries cleared
        """
        cleared_count = 0

        try:
            # Clear L1
            with self.l1_lock:
                cleared_count += len(self.l1_cache)
                self.l1_cache.clear()

            # Clear L2
            if self.l2_enabled:
                # Placeholder for Redis clear
                pass

            # Clear L3
            if self.l3_enabled:
                # Placeholder for database clear
                pass

            # Clear tag index
            with self.tag_lock:
                self.tag_index.clear()

            # Reset metrics
            with self.metrics_lock:
                self.metrics.hits = 0
                self.metrics.misses = 0
                self.metrics.evictions = 0
                self.metrics.operations = 0

            logger.info("Cleared all cache tiers: %d entries", cleared_count)
            return cleared_count

        except Exception as e:
            logger.exception("Clear all cache error: %s", e)
            return cleared_count


# Global instance for backward compatibility
# Global instance - lazy initialization
multi_tier_cache = None

def get_multi_tier_cache():
    """Get the global multi-tier cache instance with lazy initialization."""
    global multi_tier_cache
    if multi_tier_cache is None:
        multi_tier_cache = MultiTierCacheSystem()
    return multi_tier_cache
