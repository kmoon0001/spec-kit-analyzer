
import hashlib
import pickle
import shutil
from collections import OrderedDict
from datetime import UTC, datetime, timedelta
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

from src.config import get_settings

settings = get_settings()
CACHE_DIR = Path(settings.paths.cache_dir)


class CacheService:
    """A multi-level caching service for expensive computations."""

    def __init__(self, cache_dir: Path = CACHE_DIR, max_in_memory_size: int = 128):
        self.disk_cache_dir = cache_dir
        self.disk_cache_dir.mkdir(exist_ok=True)
        self.in_memory_cache = lru_cache(maxsize=max_in_memory_size)
        self._direct_cache: Dict[str, Any] = {}

    def _get_cache_key(self, func_name: str, *args, **kwargs) -> str:
        """Creates a deterministic cache key from the function and its arguments."""
        hasher = hashlib.sha256()
        hasher.update(func_name.encode())
        for arg in args:
            try:
                serialized = pickle.dumps(arg, protocol=5)
            except Exception:
                serialized = repr(arg).encode("utf-8")
            hasher.update(serialized)
        for key, value in sorted(kwargs.items()):
            hasher.update(key.encode())
            try:
                serialized = pickle.dumps(value, protocol=5)
            except Exception:
                serialized = repr(value).encode("utf-8")
            hasher.update(serialized)
        return hasher.hexdigest()

    def get_from_disk(self, key: str):
        """Retrieve an item from the disk cache."""
        cache_file = self.disk_cache_dir / key
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as handle:
                    return pickle.load(handle)
            except (pickle.UnpicklingError, EOFError):
                return None
        return None

    def set_to_disk(self, key: str, value: Any) -> None:
        """Save an item to the disk cache."""
        cache_file = self.disk_cache_dir / key
        with open(cache_file, "wb") as handle:
            pickle.dump(value, handle, protocol=5)

    def disk_cache(self, func):
        """Decorator for caching function results to disk."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            key = self._get_cache_key(func.__name__, *args, **kwargs)
            cached_result = self.get_from_disk(key)
            if cached_result is not None:
                return cached_result
            result = func(*args, **kwargs)
            self.set_to_disk(key, result)
            return result

        return wrapper

    def clear_disk_cache(self) -> None:
        """Clears all items from the disk cache."""
        self._direct_cache.clear()
        if self.disk_cache_dir.exists():
            shutil.rmtree(self.disk_cache_dir)
        self.disk_cache_dir.mkdir(exist_ok=True)

    def set(self, key: str, value: Any) -> None:
        """Store a value in both in-memory and disk caches."""
        self._direct_cache[key] = value
        self.set_to_disk(key, value)

    def get(self, key: str) -> Any:
        """Retrieve a value from cache, checking memory first then disk."""
        if key in self._direct_cache:
            return self._direct_cache[key]
        return self.get_from_disk(key)

    def delete(self, key: str) -> None:
        """Remove a cached value."""
        self._direct_cache.pop(key, None)
        cache_file = self.disk_cache_dir / key
        if cache_file.exists():
            try:
                cache_file.unlink()
            except OSError:
                pass

    def memory_cache(self, func):
        """Decorator for in-memory LRU caching."""
        return self.in_memory_cache(func)


# Singleton instance to be used across the application
cache_service = CacheService()


class MemoryAwareLRUCache:
    """An in-memory cache that tracks TTL and system memory pressure."""

    def __init__(
        self,
        *,
        max_memory_mb: int = 512,
        default_ttl_hours: float = 24.0,
        memory_pressure_threshold: int = 80,
    ) -> None:
        self.max_memory_mb = max_memory_mb
        self.memory_pressure_threshold = memory_pressure_threshold
        self.default_ttl = (
            timedelta(hours=default_ttl_hours) if default_ttl_hours > 0 else None
        )
        self.cache: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
        self.current_size_bytes: int = 0

    def _estimate_size(self, value: Any) -> int:
        try:
            return len(pickle.dumps(value, protocol=5))
        except Exception:
            return len(str(value).encode("utf-8"))

    def _delete_entry(self, key: str) -> None:
        entry = self.cache.pop(key, None)
        if entry:
            self.current_size_bytes = max(self.current_size_bytes - entry["size"], 0)

    def set(self, key: str, value: Any, ttl_hours: Optional[float] = None) -> None:
        self.clear_expired()
        ttl = ttl_hours
        if ttl is None and self.default_ttl is not None:
            ttl = self.default_ttl.total_seconds() / 3600
        expires_at: Optional[datetime]
        if ttl is not None and ttl > 0:
            expires_at = datetime.now(UTC) + timedelta(hours=ttl)
        else:
            expires_at = None

        size = self._estimate_size(value)
        if key in self.cache:
            self.current_size_bytes = max(
                self.current_size_bytes - self.cache[key]["size"], 0
            )
            del self.cache[key]

        self.cache[key] = {"value": value, "expires_at": expires_at, "size": size}
        self.cache.move_to_end(key)
        self.current_size_bytes += size
        self._cleanup_if_needed()

    def get(self, key: str) -> Optional[Any]:
        entry = self.cache.get(key)
        if entry is None:
            return None
        if entry["expires_at"] and entry["expires_at"] < datetime.now(UTC):
            self._delete_entry(key)
            return None
        self.cache.move_to_end(key)
        return entry["value"]

    def clear_expired(self) -> None:
        expired_keys = [
            key
            for key, entry in self.cache.items()
            if entry["expires_at"] and entry["expires_at"] < datetime.now(UTC)
        ]
        for key in expired_keys:
            self._delete_entry(key)

    def clear(self) -> None:
        self.cache.clear()
        self.current_size_bytes = 0

    def _current_memory_mb(self) -> float:
        return self.current_size_bytes / (1024**2)

    def _cleanup_if_needed(self) -> None:
        self.clear_expired()
        vm_percent = psutil.virtual_memory().percent
        while self.cache and (
            (self.max_memory_mb and self._current_memory_mb() > self.max_memory_mb)
            or (vm_percent >= self.memory_pressure_threshold and len(self.cache) > 1)
        ):
            key, entry = self.cache.popitem(last=False)
            self.current_size_bytes = max(self.current_size_bytes - entry["size"], 0)
            if self.cache:
                vm_percent = psutil.virtual_memory().percent
            else:
                break

    def stats(self) -> Dict[str, Any]:
        return {
            "entries": len(self.cache),
            "memory_usage_mb": round(self._current_memory_mb(), 3),
        }

    def __len__(self) -> int:  # pragma: no cover - convenience helper
        return len(self.cache)


def _hash_key(*parts: str) -> str:
    hasher = hashlib.sha256()
    for part in parts:
        if part is None:
            continue
        hasher.update(part.encode("utf-8"))
    return hasher.hexdigest()


class EmbeddingCache:
    """Cache for text embeddings keyed by content hash."""

    _cache = MemoryAwareLRUCache(max_memory_mb=384)

    @classmethod
    def get_embedding(cls, text: str) -> Optional[List[float]]:
        return cls._cache.get(_hash_key(text))

    @classmethod
    def set_embedding(cls, text: str, embedding: List[float], ttl_hours: Optional[float] = None) -> None:
        cls._cache.set(_hash_key(text), embedding, ttl_hours=ttl_hours)

    @classmethod
    def clear(cls) -> None:
        cls._cache.clear()

    @classmethod
    def entry_count(cls) -> int:
        return len(cls._cache)

    @classmethod
    def memory_usage_mb(cls) -> float:
        return cls._cache._current_memory_mb()


class NERCache:
    """Cache for NER results keyed by text and model name."""

    _cache = MemoryAwareLRUCache(max_memory_mb=256)

    @classmethod
    def get_ner_results(cls, text: str, model_name: str) -> Optional[List[Dict[str, Any]]]:
        return cls._cache.get(_hash_key(model_name, text))

    @classmethod
    def set_ner_results(
        cls,
        text: str,
        model_name: str,
        results: List[Dict[str, Any]],
        ttl_hours: Optional[float] = None,
    ) -> None:
        cls._cache.set(_hash_key(model_name, text), results, ttl_hours=ttl_hours)

    @classmethod
    def clear(cls) -> None:
        cls._cache.clear()

    @classmethod
    def entry_count(cls) -> int:
        return len(cls._cache)

    @classmethod
    def memory_usage_mb(cls) -> float:
        return cls._cache._current_memory_mb()


class DocumentCache:
    """Cache for document classification results keyed by document hash."""

    _cache = MemoryAwareLRUCache(max_memory_mb=128)

    @classmethod
    def get_document_classification(cls, doc_hash: str) -> Optional[Dict[str, Any]]:
        return cls._cache.get(doc_hash)

    @classmethod
    def set_document_classification(
        cls,
        doc_hash: str,
        classification: Dict[str, Any],
        ttl_hours: Optional[float] = None,
    ) -> None:
        cls._cache.set(doc_hash, classification, ttl_hours=ttl_hours)

    @classmethod
    def clear(cls) -> None:
        cls._cache.clear()

    @classmethod
    def entry_count(cls) -> int:
        return len(cls._cache)

    @classmethod
    def memory_usage_mb(cls) -> float:
        return cls._cache._current_memory_mb()


class LLMResponseCache:
    """Cache for LLM responses keyed by prompt and model name."""

    _cache = MemoryAwareLRUCache(max_memory_mb=256, default_ttl_hours=6)

    @classmethod
    def get_llm_response(cls, prompt: str, model_name: str) -> Optional[str]:
        return cls._cache.get(_hash_key(model_name, prompt))

    @classmethod
    def set_llm_response(
        cls,
        prompt: str,
        model_name: str,
        response: str,
        ttl_hours: Optional[float] = None,
    ) -> None:
        cls._cache.set(_hash_key(model_name, prompt), response, ttl_hours=ttl_hours)

    @classmethod
    def clear(cls) -> None:
        cls._cache.clear()

    @classmethod
    def entry_count(cls) -> int:
        return len(cls._cache)

    @classmethod
    def memory_usage_mb(cls) -> float:
        return cls._cache._current_memory_mb()


def get_cache_stats() -> Dict[str, float]:
    """Return basic statistics about in-memory caches."""
    vm = psutil.virtual_memory()
    embedding_usage = EmbeddingCache.memory_usage_mb()
    ner_usage = NERCache.memory_usage_mb()
    llm_usage = LLMResponseCache.memory_usage_mb()
    doc_usage = DocumentCache.memory_usage_mb()
    direct_entries = len(cache_service._direct_cache)
    direct_usage = 0.0
    for value in cache_service._direct_cache.values():
        try:
            direct_usage += len(pickle.dumps(value, protocol=5)) / (1024 ** 2)
        except Exception:
            direct_usage += len(str(value).encode("utf-8")) / (1024 ** 2)

    total_entries = (
        direct_entries
        + EmbeddingCache.entry_count()
        + NERCache.entry_count()
        + LLMResponseCache.entry_count()
        + DocumentCache.entry_count()
    )

    return {
        "total_entries": total_entries,
        "memory_usage_mb": round(
            direct_usage + embedding_usage + ner_usage + llm_usage + doc_usage, 3
        ),
        "system_memory_percent": float(vm.percent),
        "embedding_entries": EmbeddingCache.entry_count(),
        "ner_entries": NERCache.entry_count(),
        "llm_entries": LLMResponseCache.entry_count(),
        "doc_entries": DocumentCache.entry_count(),
        "direct_entries": direct_entries,
    }


def cleanup_all_caches() -> None:
    """Clear all in-memory and disk-based caches."""
    EmbeddingCache.clear()
    NERCache.clear()
    DocumentCache.clear()
    LLMResponseCache.clear()
    cache_service.clear_disk_cache()


__all__ = [
    "CacheService",
    "cache_service",
    "MemoryAwareLRUCache",
    "EmbeddingCache",
    "NERCache",
    "DocumentCache",
    "LLMResponseCache",
    "get_cache_stats",
    "cleanup_all_caches",
]
