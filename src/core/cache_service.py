
import hashlib
import pickle
from pathlib import Path
from functools import lru_cache, wraps
import shutil

from src.config import get_settings

settings = get_settings()
CACHE_DIR = Path(settings.paths.cache_dir)

class CacheService:
    """A multi-level caching service for expensive computations."""

    def __init__(self, cache_dir: Path = CACHE_DIR, max_in_memory_size: int = 128):
        self.disk_cache_dir = cache_dir
        self.disk_cache_dir.mkdir(exist_ok=True)
        self.in_memory_cache = lru_cache(maxsize=max_in_memory_size)

    def _get_cache_key(self, func_name: str, *args, **kwargs) -> str:
        """Creates a deterministic cache key from the function and its arguments."""
        # Serialize all arguments to ensure complex objects are handled
        # Use pickle protocol 5 for out-of-band data (more efficient)
        hasher = hashlib.sha256()
        hasher.update(func_name.encode())
        for arg in args:
            hasher.update(pickle.dumps(arg, protocol=5))
        for key, value in sorted(kwargs.items()):
            hasher.update(key.encode())
            hasher.update(pickle.dumps(value, protocol=5))
        return hasher.hexdigest()

    def get_from_disk(self, key: str):
        """Retrieve an item from the disk cache."""
        cache_file = self.disk_cache_dir / key
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    return pickle.load(f)
            except (pickle.UnpicklingError, EOFError):
                # Handle corrupted cache files gracefully
                return None
        return None

    def set_to_disk(self, key: str, value: Any):
        """Save an item to the disk cache."""
        cache_file = self.disk_cache_dir / key
        with open(cache_file, "wb") as f:
            pickle.dump(value, f, protocol=5)

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

    def clear_disk_cache(self):
        """Clears all items from the disk cache."""
        if self.disk_cache_dir.exists():
            shutil.rmtree(self.disk_cache_dir)
        self.disk_cache_dir.mkdir(exist_ok=True)

    def memory_cache(self, func):
        """Decorator for in-memory LRU caching."""
        return self.in_memory_cache(func)

# Singleton instance to be used across the application
cache_service = CacheService()
