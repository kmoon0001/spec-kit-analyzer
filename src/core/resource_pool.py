"""Resource Pool Management for Therapy Compliance Analyzer

This module provides intelligent resource pooling and lifecycle management
for expensive resources like AI models, database connections, and large
data structures.
"""

import logging
import queue
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ResourceState(Enum):
    """Resource lifecycle states."""

    CREATING = "creating"
    AVAILABLE = "available"
    IN_USE = "in_use"
    IDLE = "idle"
    EXPIRED = "expired"
    DISPOSED = "disposed"


@dataclass
class ResourceMetrics:
    """Metrics for a pooled resource."""

    created_at: datetime
    last_used: datetime
    use_count: int
    total_use_time: timedelta
    average_use_time: timedelta
    state: ResourceState


class PooledResource(Generic[T]):
    """Wrapper for pooled resources with lifecycle management."""

    def __init__(self, resource: T, resource_id: str, pool: "ResourcePool"):
        self.resource = resource
        self.resource_id = resource_id
        self.pool = pool
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.use_count = 0
        self.total_use_time = timedelta()
        self.average_use_time = timedelta()
        self.state = ResourceState.AVAILABLE
        self._use_start_time: datetime | None = None
        self._lock = threading.Lock()

    def acquire(self) -> T:
        """Acquire the resource for use."""
        with self._lock:
            if self.state != ResourceState.AVAILABLE:
                raise RuntimeError(f"Resource {self.resource_id} is not available (state: {self.state})")

            self.state = ResourceState.IN_USE
            self.last_used = datetime.now()
            self._use_start_time = self.last_used
            self.use_count += 1

            logger.debug("Resource %s acquired (use #{self.use_count})", self.resource_id)
            return self.resource

    def release(self) -> None:
        """Release the resource back to the pool."""
        with self._lock:
            if self.state != ResourceState.IN_USE:
                logger.warning("Attempting to release resource %s that is not in use", self.resource_id)
                return

            if self._use_start_time:
                use_duration = datetime.now() - self._use_start_time
                self.total_use_time += use_duration
                self.average_use_time = self.total_use_time / self.use_count
                self._use_start_time = None

            self.state = ResourceState.AVAILABLE
            logger.debug("Resource %s released", self.resource_id)

            # Notify pool that resource is available
            self.pool._on_resource_released(self)

    def mark_expired(self) -> None:
        """Mark resource as expired."""
        with self._lock:
            if self.state in [ResourceState.AVAILABLE, ResourceState.IDLE]:
                self.state = ResourceState.EXPIRED
                logger.debug("Resource %s marked as expired", self.resource_id)

    def dispose(self) -> None:
        """Dispose of the resource."""
        with self._lock:
            self.state = ResourceState.DISPOSED
            logger.debug("Resource %s disposed", self.resource_id)

    def get_metrics(self) -> ResourceMetrics:
        """Get resource metrics."""
        with self._lock:
            return ResourceMetrics(
                created_at=self.created_at,
                last_used=self.last_used,
                use_count=self.use_count,
                total_use_time=self.total_use_time,
                average_use_time=self.average_use_time,
                state=self.state,
            )

    def __enter__(self) -> T:
        """Context manager entry."""
        return self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.release()


class ResourceFactory(ABC, Generic[T]):
    """Abstract factory for creating pooled resources."""

    @abstractmethod
    def create_resource(self, resource_id: str) -> T:
        """Create a new resource instance."""

    @abstractmethod
    def validate_resource(self, resource: T) -> bool:
        """Validate that a resource is still usable."""

    @abstractmethod
    def dispose_resource(self, resource: T) -> None:
        """Dispose of a resource properly."""

    def get_resource_size(self, resource: T) -> int:
        """Get estimated memory size of resource in bytes."""
        return 0  # Override in subclasses if size tracking is needed


@dataclass
class PoolConfiguration:
    """Configuration for resource pools."""

    min_size: int = 1
    max_size: int = 10
    max_idle_time: timedelta = timedelta(minutes=30)
    max_lifetime: timedelta = timedelta(hours=2)
    validation_interval: timedelta = timedelta(minutes=5)
    preload_resources: bool = True
    enable_metrics: bool = True


class ResourcePool(Generic[T]):
    """Generic resource pool with lifecycle management."""

    def __init__(self, name: str, factory: ResourceFactory[T],
                 config: PoolConfiguration):
        self.name = name
        self.factory = factory
        self.config = config

        self._resources: dict[str, PooledResource[T]] = {}
        self._available_queue: queue.Queue = queue.Queue()
        self._lock = threading.RLock()
        self._next_id = 0
        self._shutdown = False

        # Start maintenance thread
        self._maintenance_thread = threading.Thread(
            target=self._maintenance_loop,
            daemon=True,
            name=f"ResourcePool-{name}-Maintenance",
        )
        self._maintenance_thread.start()

        # Preload resources if configured
        if config.preload_resources:
            self._preload_resources()

        logger.info("Resource pool '%s' initialized with config: {config}", name)

    def acquire_resource(self, timeout: float | None = None) -> PooledResource[T] | None:
        """Acquire a resource from the pool."""
        if self._shutdown:
            raise RuntimeError(f"Resource pool '{self.name}' is shut down")

        # Try to get an available resource
        try:
            while True:
                try:
                    resource_id = self._available_queue.get_nowait()
                    with self._lock:
                        if resource_id in self._resources:
                            pooled_resource = self._resources[resource_id]
                            if pooled_resource.state == ResourceState.AVAILABLE:
                                return pooled_resource
                except queue.Empty:
                    break
        except Exception as e:
            logger.exception("Error getting available resource: %s", e)

        # No available resources, try to create a new one
        with self._lock:
            if len(self._resources) < self.config.max_size:
                return self._create_resource()

        # Pool is full, wait for a resource to become available
        if timeout is not None:
            try:
                resource_id = self._available_queue.get(timeout=timeout)
                with self._lock:
                    if resource_id in self._resources:
                        pooled_resource = self._resources[resource_id]
                        if pooled_resource.state == ResourceState.AVAILABLE:
                            return pooled_resource
            except queue.Empty:
                logger.warning("Timeout waiting for resource in pool '%s'", self.name)
                return None

        return None

    def release_resource(self, pooled_resource: PooledResource[T]) -> None:
        """Release a resource back to the pool."""
        pooled_resource.release()

    def get_pool_status(self) -> dict[str, Any]:
        """Get current pool status and metrics."""
        with self._lock:
            total_resources = len(self._resources)
            available_count = sum(1 for r in self._resources.values()
                                if r.state == ResourceState.AVAILABLE)
            in_use_count = sum(1 for r in self._resources.values()
                             if r.state == ResourceState.IN_USE)
            expired_count = sum(1 for r in self._resources.values()
                              if r.state == ResourceState.EXPIRED)

            # Calculate average metrics
            total_uses = sum(r.use_count for r in self._resources.values())
            avg_use_count = total_uses / total_resources if total_resources > 0 else 0

            return {
                "name": self.name,
                "total_resources": total_resources,
                "available": available_count,
                "in_use": in_use_count,
                "expired": expired_count,
                "queue_size": self._available_queue.qsize(),
                "average_use_count": avg_use_count,
                "config": {
                    "min_size": self.config.min_size,
                    "max_size": self.config.max_size,
                    "max_idle_time": str(self.config.max_idle_time),
                    "max_lifetime": str(self.config.max_lifetime),
                },
            }

    def get_resource_metrics(self) -> list[ResourceMetrics]:
        """Get metrics for all resources in the pool."""
        with self._lock:
            return [resource.get_metrics() for resource in self._resources.values()]

    def shutdown(self) -> None:
        """Shutdown the resource pool."""
        self._shutdown = True

        with self._lock:
            # Dispose of all resources
            for resource in self._resources.values():
                try:
                    self.factory.dispose_resource(resource.resource)
                    resource.dispose()
                except Exception as e:
                    logger.exception("Error disposing resource: %s", e)

            self._resources.clear()

        logger.info("Resource pool '%s' shut down", self.name)

    def _create_resource(self) -> PooledResource[T]:
        """Create a new pooled resource."""
        resource_id = f"{self.name}-{self._next_id}"
        self._next_id += 1

        try:
            resource = self.factory.create_resource(resource_id)
            pooled_resource = PooledResource(resource, resource_id, self)
            self._resources[resource_id] = pooled_resource

            logger.debug("Created new resource: %s", resource_id)
            return pooled_resource

        except Exception as e:
            logger.exception("Failed to create resource %s: {e}", resource_id)
            raise

    def _preload_resources(self) -> None:
        """Preload minimum number of resources."""
        with self._lock:
            for _ in range(self.config.min_size):
                try:
                    resource = self._create_resource()
                    self._available_queue.put(resource.resource_id)
                except Exception as e:
                    logger.exception("Failed to preload resource: %s", e)
                    break

    def _on_resource_released(self, pooled_resource: PooledResource[T]) -> None:
        """Handle resource release notification."""
        if not self._shutdown and pooled_resource.state == ResourceState.AVAILABLE:
            self._available_queue.put(pooled_resource.resource_id)

    def _maintenance_loop(self) -> None:
        """Background maintenance loop."""
        while not self._shutdown:
            try:
                self._cleanup_expired_resources()
                self._validate_resources()
                self._ensure_minimum_resources()

                time.sleep(self.config.validation_interval.total_seconds())

            except (ValueError, TypeError, AttributeError) as e:
                logger.exception("Error in resource pool maintenance: %s", e)
                time.sleep(5)  # Brief pause before retrying

    def _cleanup_expired_resources(self) -> None:
        """Clean up expired and old resources."""
        now = datetime.now()
        expired_resources = []

        with self._lock:
            for resource_id, resource in self._resources.items():
                # Check if resource has exceeded maximum lifetime
                if now - resource.created_at > self.config.max_lifetime:
                    resource.mark_expired()
                    expired_resources.append(resource_id)
                    continue

                # Check if resource has been idle too long
                if (resource.state == ResourceState.AVAILABLE and
                    now - resource.last_used > self.config.max_idle_time):
                    resource.mark_expired()
                    expired_resources.append(resource_id)

            # Remove expired resources
            for resource_id in expired_resources:
                if resource_id in self._resources:
                    resource = self._resources[resource_id]
                    try:
                        self.factory.dispose_resource(resource.resource)
                        resource.dispose()
                        del self._resources[resource_id]
                        logger.debug("Cleaned up expired resource: %s", resource_id)
                    except Exception as e:
                        logger.exception("Error disposing expired resource %s: {e}", resource_id)

    def _validate_resources(self) -> None:
        """Validate that resources are still usable."""
        invalid_resources = []

        with self._lock:
            for resource_id, resource in self._resources.items():
                if resource.state == ResourceState.AVAILABLE:
                    try:
                        if not self.factory.validate_resource(resource.resource):
                            resource.mark_expired()
                            invalid_resources.append(resource_id)
                    except (ValueError, TypeError, AttributeError) as e:
                        logger.exception("Error validating resource %s: {e}", resource_id)
                        resource.mark_expired()
                        invalid_resources.append(resource_id)

            # Remove invalid resources
            for resource_id in invalid_resources:
                if resource_id in self._resources:
                    resource = self._resources[resource_id]
                    try:
                        self.factory.dispose_resource(resource.resource)
                        resource.dispose()
                        del self._resources[resource_id]
                        logger.debug("Removed invalid resource: %s", resource_id)
                    except Exception as e:
                        logger.exception("Error disposing invalid resource %s: {e}", resource_id)

    def _ensure_minimum_resources(self) -> None:
        """Ensure minimum number of resources are available."""
        with self._lock:
            available_count = sum(1 for r in self._resources.values()
                                if r.state == ResourceState.AVAILABLE)

            needed = self.config.min_size - available_count
            for _ in range(needed):
                if len(self._resources) < self.config.max_size:
                    try:
                        resource = self._create_resource()
                        self._available_queue.put(resource.resource_id)
                    except Exception as e:
                        logger.exception("Failed to create minimum resource: %s", e)
                        break


class ResourcePoolManager:
    """Manager for multiple resource pools."""

    def __init__(self):
        self._pools: dict[str, ResourcePool] = {}
        self._lock = threading.Lock()

    def create_pool(self, name: str, factory: ResourceFactory[T],
                   config: PoolConfiguration) -> ResourcePool[T]:
        """Create a new resource pool."""
        with self._lock:
            if name in self._pools:
                raise ValueError(f"Pool '{name}' already exists")

            pool = ResourcePool(name, factory, config)
            self._pools[name] = pool
            return pool

    def get_pool(self, name: str) -> ResourcePool | None:
        """Get a resource pool by name."""
        with self._lock:
            return self._pools.get(name)

    def get_all_pools_status(self) -> dict[str, dict[str, Any]]:
        """Get status of all pools."""
        with self._lock:
            return {name: pool.get_pool_status() for name, pool in self._pools.items()}

    def shutdown_all(self) -> None:
        """Shutdown all resource pools."""
        with self._lock:
            for pool in self._pools.values():
                try:
                    pool.shutdown()
                except Exception as e:
                    logger.exception("Error shutting down pool: %s", e)

            self._pools.clear()
            logger.info("All resource pools shut down")


# Global resource pool manager instance
resource_pool_manager = ResourcePoolManager()
