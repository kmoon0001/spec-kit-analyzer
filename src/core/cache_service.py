
import hashlib
import json
import pickle
import shutil
from datetime import UTC, datetime, timedelta
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any

import psutil  # type: ignore[import-untyped]

from src.config import get_settings

settings = get_settings()
CACHE_DIR = Path(settings.paths.cache_dir)

class CacheService:
    """A multi-level caching service for expensive computations."""

    def __init__(self, cache_dir: Path = CACHE_DIR, max_in_memory_size: int = 128):
        self.disk_cache_dir = cache_dir
        self.disk_cache_dir.mkdir(exist_ok=True)
        self.in_memory_cache = lru_cache(maxsize=max_in_memory_size)
        self._direct_cache: dict[str, Any] = {}

    def _get_cache_key(self, func_name: str, *args, **kwargs) -> str:
        """Creates a deterministic cache key from the function and its arguments."""
        hasher = hashlib.sha256()
        hasher.update(func_name.encode())
        for arg in args:
            try:
                serialized = pickle.dumps(arg, protocol=5)
            except (ValueError, json.JSONDecodeError):
                serialized = repr(arg).encode("utf-8")
            hasher.update(serialized)
        for key, value in sorted(kwargs.items()):
            hasher.update(key.encode())
            try:
                serialized = pickle.dumps(value, protocol=5)
            except (ValueError, json.JSONDecodeError):
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
# Singleton instance to be used across the application
# Singleton instance to be used across the application
cache_service = CacheService()

class MemoryAwareLRUCache:
    """An in-memory cache that tracks TTL and system memory pressure."""
    
    def __init__(self, max_memory_mb: int = 512):
        from collections import OrderedDict
        self.cache = OrderedDict()
        self.current_size_bytes = 0
        self.max_memory_mb = max_memory_mb
        self.memory_pressure_threshold = 85

    def _estimate_size(self, value: Any) -> int:
        try:
            return len(pickle.dumps(value, protocol=5))
        except (ValueError, json.JSONDecodeError):
            return len(str(value).encode("utf-8"))

    def _delete_entry(self, key: str) -> None:
        entry = self.cache.pop(key, None)
        if entry:
            self.current_size_bytes = max(self.current_size_bytes - entry["size"], 0)

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
    
    def get(self, key: str, default=None):
        """Get a value from the cache."""
        entry = self.cache.get(key)
        if entry is None:
            return default
        
        # Check if expired
        if entry["expires_at"] and entry["expires_at"] < datetime.now(UTC):
            self._delete_entry(key)
            return default
        
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl_seconds: int = None, ttl_hours: float = None):
        """Set a value in the cache with optional TTL."""
        # Remove existing entry if it exists
        if key in self.cache:
            self._delete_entry(key)
        
        # Calculate size and expiration
        size = self._estimate_size(value)
        
        # Handle both ttl_seconds and ttl_hours
        if ttl_hours is not None:
            ttl_seconds = int(ttl_hours * 3600)
        
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds) if ttl_seconds else None
        
        # Store the entry
        self.cache[key] = {
            "value": value,
            "size": size,
            "expires_at": expires_at,
            "created_at": datetime.now(UTC)
        }
        self.current_size_bytes += size

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

    def stats(self) -> dict[str, Any]:
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

    _cache = MemoryAwareLRUCache()

    @classmethod
    def get_embedding(cls, text: str) -> list[float] | None:
        return cls._cache.get(_hash_key(text))

    @classmethod
    def set_embedding(cls, text: str, embedding: list[float], ttl_hours: float | None = None) -> None:
        cls._cache.set(_hash_key(text), embedding, ttl_hours=ttl_hours)

    @classmethod
    def entry_count(cls) -> int:
        return len(cls._cache)

    @classmethod
    def memory_usage_mb(cls) -> float:
        return cls._cache._current_memory_mb()
    
    @classmethod
    def clear(cls) -> None:
        cls._cache.clear()
    
    @classmethod
    def memory_usage_mb(cls) -> float:
        return cls._cache._current_memory_mb()

class NERCache:
    """Cache for NER results keyed by text and model name."""

    _cache = MemoryAwareLRUCache()

    @classmethod
    def get_ner_results(cls, text: str, model_name: str) -> list[dict[str, Any]] | None:
        return cls._cache.get(_hash_key(model_name, text))

    @classmethod
    def set_ner_results(
        cls,
        text: str,
        model_name: str,
        results: list[dict[str, Any]],
        ttl_hours: float | None = None) -> None:
        cls._cache.set(_hash_key(model_name, text), results, ttl_hours=ttl_hours)

    @classmethod
    def get_document_classification(cls, doc_hash: str) -> dict[str, Any] | None:
        return cls._cache.get(doc_hash)

    @classmethod
    def set_document_classification(
        cls,
        doc_hash: str,
        classification: dict[str, Any],
        ttl_hours: float | None = None) -> None:
        cls._cache.set(doc_hash, classification, ttl_hours=ttl_hours)

    @classmethod
    def get_llm_response(cls, prompt: str, model_name: str) -> str | None:
        return cls._cache.get(_hash_key(model_name, prompt))

    @classmethod
    def set_llm_response(
        cls,
        prompt: str,
        model_name: str,
        response: str,
        ttl_hours: float | None = None) -> None:
        cls._cache.set(_hash_key(model_name, prompt), response, ttl_hours=ttl_hours)
    
    @classmethod
    def memory_usage_mb(cls) -> float:
        return cls._cache._current_memory_mb()
    
    @classmethod
    def entry_count(cls) -> int:
        return len(cls._cache)

def get_cache_stats() -> dict[str, float]:
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
        except (ValueError, json.JSONDecodeError):
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
            direct_usage + embedding_usage + ner_usage + llm_usage + doc_usage, 3),
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
    "cleanup_all_caches"]



class LLMResponseCache:
    """LLM response cache implementation."""
    _cache = {}

    @classmethod
    def get_response(cls, model_name: str, prompt: str) -> str | None:
        return cls._cache.get(f"{model_name}:{prompt}")
    
    @classmethod
    def get_llm_response(cls, model_name: str, prompt: str) -> str | None:
        return cls.get_response(model_name, prompt)

    @classmethod
    def set_response(cls, model_name: str, prompt: str, response: str, ttl_hours: int = 24):
        cls._cache[f"{model_name}:{prompt}"] = response
    
    @classmethod
    def set_llm_response(cls, model_name: str, prompt: str, response: str, ttl_hours: int = 24):
        cls.set_response(model_name, prompt, response, ttl_hours)
    
    @classmethod
    def memory_usage_mb(cls) -> float:
        """Estimate memory usage of LLM response cache."""
        total_bytes = 0
        for key, value in cls._cache.items():
            total_bytes += len(str(key).encode('utf-8'))
            total_bytes += len(str(value).encode('utf-8'))
        return total_bytes / (1024 * 1024)
    
    @classmethod
    def entry_count(cls) -> int:
        return len(cls._cache)

class DocumentCache:
    """Document cache implementation."""
    _cache = {}

    @classmethod
    def get_document(cls, doc_id: str) -> dict | None:
        return cls._cache.get(doc_id)

    @classmethod
    def set_document(cls, doc_id: str, document: dict):
        cls._cache[doc_id] = document
    
    @classmethod
    def get_document_classification(cls, doc_id: str) -> str | None:
        doc = cls._cache.get(doc_id)
        return doc.get('classification') if doc else None
    
    @classmethod
    def memory_usage_mb(cls) -> float:
        """Estimate memory usage of document cache."""
        total_bytes = 0
        for key, value in cls._cache.items():
            total_bytes += len(str(key).encode('utf-8'))
            try:
                import pickle
                total_bytes += len(pickle.dumps(value))
            except:
                total_bytes += len(str(value).encode('utf-8'))
        return total_bytes / (1024 * 1024)
    
    @classmethod
    def entry_count(cls) -> int:
        return len(cls._cache)
