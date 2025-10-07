"""
Tests for Resource Pool Management System

This module tests the resource pooling, lifecycle management, and factory
components of the resource management system.
"""

import pytest
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Any

from src.core.resource_pool import (
    ResourcePool, PooledResource, ResourceFactory, PoolConfiguration,
    ResourceState, ResourceMetrics, ResourcePoolManager, resource_pool_manager
)


class MockResource:
    """Mock resource for testing."""
    
    def __init__(self, resource_id: str, fail_validation: bool = False):
        self.resource_id = resource_id
        self.fail_validation = fail_validation
        self.disposed = False
    
    def do_work(self) -> str:
        """Simulate resource work."""
        return f"Work done by {self.resource_id}"


class MockResourceFactory(ResourceFactory[MockResource]):
    """Mock resource factory for testing."""
    
    def __init__(self, fail_creation: bool = False, fail_validation: bool = False):
        self.fail_creation = fail_creation
        self.fail_validation = fail_validation
        self.created_resources = []
        self.disposed_resources = []
    
    def create_resource(self, resource_id: str) -> MockResource:
        """Create a mock resource."""
        if self.fail_creation:
            raise RuntimeError(f"Failed to create resource {resource_id}")
        
        resource = MockResource(resource_id, self.fail_validation)
        self.created_resources.append(resource)
        return resource
    
    def validate_resource(self, resource: MockResource) -> bool:
        """Validate a mock resource."""
        return not resource.fail_validation and not resource.disposed
    
    def dispose_resource(self, resource: MockResource) -> None:
        """Dispose of a mock resource."""
        resource.disposed = True
        self.disposed_resources.append(resource)
    
    def get_resource_size(self, resource: MockResource) -> int:
        """Get mock resource size."""
        return 1024  # 1KB


class TestPooledResource:
    """Test pooled resource wrapper functionality."""
    
    def test_pooled_resource_initialization(self):
        """Test pooled resource initialization."""
        mock_pool = Mock()
        resource = MockResource("test-1")
        
        pooled = PooledResource(resource, "test-1", mock_pool)
        
        assert pooled.resource == resource
        assert pooled.resource_id == "test-1"
        assert pooled.pool == mock_pool
        assert pooled.state == ResourceState.AVAILABLE
        assert pooled.use_count == 0
    
    def test_resource_acquire_release_cycle(self):
        """Test resource acquire/release cycle."""
        mock_pool = Mock()
        resource = MockResource("test-1")
        pooled = PooledResource(resource, "test-1", mock_pool)
        
        # Acquire resource
        acquired = pooled.acquire()
        assert acquired == resource
        assert pooled.state == ResourceState.IN_USE
        assert pooled.use_count == 1
        
        # Release resource
        pooled.release()
        assert pooled.state == ResourceState.AVAILABLE
        mock_pool._on_resource_released.assert_called_once_with(pooled)
    
    def test_context_manager_usage(self):
        """Test using pooled resource as context manager."""
        mock_pool = Mock()
        resource = MockResource("test-1")
        pooled = PooledResource(resource, "test-1", mock_pool)
        
        with pooled as acquired_resource:
            assert acquired_resource == resource
            assert pooled.state == ResourceState.IN_USE
        
        assert pooled.state == ResourceState.AVAILABLE
        mock_pool._on_resource_released.assert_called_once()
    
    def test_resource_metrics_tracking(self):
        """Test resource metrics tracking."""
        mock_pool = Mock()
        resource = MockResource("test-1")
        pooled = PooledResource(resource, "test-1", mock_pool)
        
        # Use resource multiple times
        for _ in range(3):
            with pooled:
                time.sleep(0.01)  # Simulate work
        
        metrics = pooled.get_metrics()
        assert metrics.use_count == 3
        assert metrics.state == ResourceState.AVAILABLE
        assert metrics.total_use_time > timedelta(0)
        assert metrics.average_use_time > timedelta(0)
    
    def test_invalid_state_transitions(self):
        """Test invalid state transitions."""
        mock_pool = Mock()
        resource = MockResource("test-1")
        pooled = PooledResource(resource, "test-1", mock_pool)
        
        # Try to acquire already acquired resource
        pooled.acquire()
        with pytest.raises(RuntimeError, match="not available"):
            pooled.acquire()
        
        # Release and try to release again
        pooled.release()
        pooled.release()  # Should not raise, but should log warning


class TestResourceFactory:
    """Test resource factory functionality."""
    
    def test_factory_creation_success(self):
        """Test successful resource creation."""
        factory = MockResourceFactory()
        
        resource = factory.create_resource("test-1")
        
        assert isinstance(resource, MockResource)
        assert resource.resource_id == "test-1"
        assert len(factory.created_resources) == 1
    
    def test_factory_creation_failure(self):
        """Test resource creation failure."""
        factory = MockResourceFactory(fail_creation=True)
        
        with pytest.raises(RuntimeError, match="Failed to create"):
            factory.create_resource("test-1")
    
    def test_factory_validation(self):
        """Test resource validation."""
        factory = MockResourceFactory()
        
        # Valid resource
        resource = MockResource("test-1")
        assert factory.validate_resource(resource)
        
        # Invalid resource
        invalid_resource = MockResource("test-2", fail_validation=True)
        assert not factory.validate_resource(invalid_resource)
    
    def test_factory_disposal(self):
        """Test resource disposal."""
        factory = MockResourceFactory()
        resource = MockResource("test-1")
        
        factory.dispose_resource(resource)
        
        assert resource.disposed
        assert len(factory.disposed_resources) == 1


class TestResourcePool:
    """Test resource pool functionality."""
    
    def test_pool_initialization(self):
        """Test resource pool initialization."""
        factory = MockResourceFactory()
        config = PoolConfiguration(min_size=2, max_size=5, preload_resources=False)
        
        pool = ResourcePool("test-pool", factory, config)
        
        assert pool.name == "test-pool"
        assert pool.factory == factory
        assert pool.config == config
        assert not pool._shutdown
    
    def test_pool_preloading(self):
        """Test resource pool preloading."""
        factory = MockResourceFactory()
        config = PoolConfiguration(min_size=3, max_size=5, preload_resources=True)
        
        pool = ResourcePool("test-pool", factory, config)
        
        # Wait a bit for preloading to complete
        time.sleep(0.1)
        
        status = pool.get_pool_status()
        assert status['total_resources'] >= config.min_size
        assert len(factory.created_resources) >= config.min_size
    
    def test_resource_acquisition_and_release(self):
        """Test resource acquisition and release."""
        factory = MockResourceFactory()
        config = PoolConfiguration(min_size=1, max_size=3, preload_resources=True)
        
        pool = ResourcePool("test-pool", factory, config)
        time.sleep(0.1)  # Wait for preloading
        
        # Acquire resource
        pooled_resource = pool.acquire_resource()
        assert pooled_resource is not None
        assert pooled_resource.state == ResourceState.AVAILABLE
        
        # Use resource
        with pooled_resource as resource:
            assert isinstance(resource, MockResource)
            result = resource.do_work()
            assert "Work done by" in result
        
        # Resource should be available again
        assert pooled_resource.state == ResourceState.AVAILABLE
    
    def test_pool_size_limits(self):
        """Test pool size limits."""
        factory = MockResourceFactory()
        config = PoolConfiguration(min_size=1, max_size=2, preload_resources=False)
        
        pool = ResourcePool("test-pool", factory, config)
        
        # Acquire maximum number of resources
        resources = []
        for _ in range(config.max_size):
            resource = pool.acquire_resource()
            assert resource is not None
            resource.acquire()  # Mark as in use
            resources.append(resource)
        
        # Try to acquire one more (should fail or timeout)
        extra_resource = pool.acquire_resource(timeout=0.1)
        assert extra_resource is None
        
        # Release one resource
        resources[0].release()
        
        # Now should be able to acquire again
        new_resource = pool.acquire_resource()
        assert new_resource is not None
    
    def test_pool_status_reporting(self):
        """Test pool status reporting."""
        factory = MockResourceFactory()
        config = PoolConfiguration(min_size=2, max_size=5, preload_resources=True)
        
        pool = ResourcePool("test-pool", factory, config)
        time.sleep(0.1)  # Wait for preloading
        
        status = pool.get_pool_status()
        
        assert status['name'] == "test-pool"
        assert status['total_resources'] >= 2
        assert status['available'] >= 0
        assert status['in_use'] >= 0
        assert 'config' in status
        assert status['config']['min_size'] == 2
        assert status['config']['max_size'] == 5
    
    def test_resource_metrics_collection(self):
        """Test resource metrics collection."""
        factory = MockResourceFactory()
        config = PoolConfiguration(min_size=1, max_size=3, preload_resources=True)
        
        pool = ResourcePool("test-pool", factory, config)
        time.sleep(0.1)  # Wait for preloading
        
        # Use a resource
        pooled_resource = pool.acquire_resource()
        with pooled_resource:
            time.sleep(0.01)
        
        metrics = pool.get_resource_metrics()
        assert len(metrics) > 0
        assert all(isinstance(m, ResourceMetrics) for m in metrics)
    
    def test_pool_shutdown(self):
        """Test pool shutdown."""
        factory = MockResourceFactory()
        config = PoolConfiguration(min_size=2, max_size=5, preload_resources=True)
        
        pool = ResourcePool("test-pool", factory, config)
        time.sleep(0.1)  # Wait for preloading
        
        initial_resources = len(factory.created_resources)
        
        pool.shutdown()
        
        assert pool._shutdown
        assert len(factory.disposed_resources) == initial_resources
        
        # Should not be able to acquire resources after shutdown
        with pytest.raises(RuntimeError, match="shut down"):
            pool.acquire_resource()
    
    def test_maintenance_loop_cleanup(self):
        """Test maintenance loop resource cleanup."""
        factory = MockResourceFactory()
        config = PoolConfiguration(
            min_size=1, max_size=3, preload_resources=True,
            max_idle_time=timedelta(milliseconds=50),
            validation_interval=timedelta(milliseconds=100)
        )
        
        pool = ResourcePool("test-pool", factory, config)
        time.sleep(0.1)  # Wait for preloading
        
        initial_count = len(factory.created_resources)
        
        # Wait for maintenance to run and clean up idle resources
        time.sleep(0.2)
        
        # Should have cleaned up some resources
        final_count = len(factory.created_resources) - len(factory.disposed_resources)
        assert final_count >= config.min_size  # Should maintain minimum
        
        pool.shutdown()
    
    def test_invalid_resource_handling(self):
        """Test handling of invalid resources."""
        factory = MockResourceFactory(fail_validation=True)
        config = PoolConfiguration(
            min_size=1, max_size=3, preload_resources=True,
            validation_interval=timedelta(milliseconds=50)
        )
        
        pool = ResourcePool("test-pool", factory, config)
        time.sleep(0.1)  # Wait for preloading and validation
        
        # Wait for validation to run
        time.sleep(0.1)
        
        # Invalid resources should be cleaned up
        assert len(factory.disposed_resources) > 0
        
        pool.shutdown()


class TestResourcePoolManager:
    """Test resource pool manager functionality."""
    
    def test_pool_creation_and_retrieval(self):
        """Test pool creation and retrieval."""
        manager = ResourcePoolManager()
        factory = MockResourceFactory()
        config = PoolConfiguration(min_size=1, max_size=3)
        
        # Create pool
        pool = manager.create_pool("test-pool", factory, config)
        assert pool is not None
        assert pool.name == "test-pool"
        
        # Retrieve pool
        retrieved_pool = manager.get_pool("test-pool")
        assert retrieved_pool == pool
        
        # Try to create duplicate pool
        with pytest.raises(ValueError, match="already exists"):
            manager.create_pool("test-pool", factory, config)
        
        manager.shutdown_all()
    
    def test_pool_status_aggregation(self):
        """Test aggregated pool status reporting."""
        manager = ResourcePoolManager()
        factory1 = MockResourceFactory()
        factory2 = MockResourceFactory()
        config = PoolConfiguration(min_size=1, max_size=3, preload_resources=False)
        
        # Create multiple pools
        pool1 = manager.create_pool("pool-1", factory1, config)
        pool2 = manager.create_pool("pool-2", factory2, config)
        
        # Get all pool statuses
        all_status = manager.get_all_pools_status()
        
        assert len(all_status) == 2
        assert "pool-1" in all_status
        assert "pool-2" in all_status
        assert all_status["pool-1"]["name"] == "pool-1"
        assert all_status["pool-2"]["name"] == "pool-2"
        
        manager.shutdown_all()
    
    def test_manager_shutdown(self):
        """Test manager shutdown functionality."""
        manager = ResourcePoolManager()
        factory = MockResourceFactory()
        config = PoolConfiguration(min_size=2, max_size=5, preload_resources=True)
        
        # Create pools
        pool1 = manager.create_pool("pool-1", factory, config)
        pool2 = manager.create_pool("pool-2", factory, config)
        
        time.sleep(0.1)  # Wait for preloading
        
        # Shutdown all pools
        manager.shutdown_all()
        
        # Pools should be shut down
        assert pool1._shutdown
        assert pool2._shutdown
        
        # Manager should have no pools
        assert len(manager._pools) == 0
    
    def test_nonexistent_pool_retrieval(self):
        """Test retrieving nonexistent pool."""
        manager = ResourcePoolManager()
        
        pool = manager.get_pool("nonexistent")
        assert pool is None


class TestIntegration:
    """Integration tests for resource pool system."""
    
    def test_concurrent_resource_usage(self):
        """Test concurrent resource usage."""
        factory = MockResourceFactory()
        config = PoolConfiguration(min_size=2, max_size=4, preload_resources=True)
        
        pool = ResourcePool("concurrent-pool", factory, config)
        time.sleep(0.1)  # Wait for preloading
        
        results = []
        errors = []
        
        def worker(worker_id: int):
            try:
                pooled_resource = pool.acquire_resource(timeout=1.0)
                if pooled_resource:
                    with pooled_resource as resource:
                        result = resource.do_work()
                        time.sleep(0.01)  # Simulate work
                        results.append(f"Worker {worker_id}: {result}")
                else:
                    errors.append(f"Worker {worker_id}: Failed to acquire resource")
            except Exception as e:
                errors.append(f"Worker {worker_id}: {str(e)}")
        
        # Start multiple worker threads
        threads = []
        for i in range(6):  # More workers than max pool size
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=2.0)
        
        # Check results
        assert len(results) > 0, f"No successful results. Errors: {errors}"
        assert len(errors) <= 2, f"Too many errors: {errors}"  # Some workers might timeout
        
        pool.shutdown()
    
    def test_resource_lifecycle_with_failures(self):
        """Test resource lifecycle with various failure scenarios."""
        factory = MockResourceFactory()
        config = PoolConfiguration(
            min_size=1, max_size=3, preload_resources=True,
            max_idle_time=timedelta(milliseconds=100),
            validation_interval=timedelta(milliseconds=50)
        )
        
        pool = ResourcePool("lifecycle-pool", factory, config)
        time.sleep(0.1)  # Wait for preloading
        
        # Normal usage
        pooled_resource = pool.acquire_resource()
        assert pooled_resource is not None
        
        with pooled_resource as resource:
            result = resource.do_work()
            assert "Work done by" in result
        
        # Simulate resource becoming invalid
        pooled_resource.resource.fail_validation = True
        
        # Wait for validation to detect and clean up invalid resource
        time.sleep(0.15)
        
        # Pool should still be functional
        new_resource = pool.acquire_resource()
        assert new_resource is not None
        
        pool.shutdown()
    
    def test_global_resource_pool_manager(self):
        """Test global resource pool manager instance."""
        # Use the global instance
        factory = MockResourceFactory()
        config = PoolConfiguration(min_size=1, max_size=2, preload_resources=False)
        
        # Create pool using global manager
        pool = resource_pool_manager.create_pool("global-test", factory, config)
        assert pool is not None
        
        # Retrieve using global manager
        retrieved = resource_pool_manager.get_pool("global-test")
        assert retrieved == pool
        
        # Clean up
        resource_pool_manager.shutdown_all()


if __name__ == "__main__":
    pytest.main([__file__])
