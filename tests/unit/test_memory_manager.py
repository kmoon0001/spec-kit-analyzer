"""
Tests for Memory Management System

This module tests the memory monitoring, resource tracking, and optimization
components of the memory management system.
"""

import pytest
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.core.memory_manager import (
    MemoryMonitor, ResourceTracker, MemoryOptimizer, MemoryManager,
    MemoryPressureLevel, ResourceAllocation
)


class TestMemoryMonitor:
    """Test memory monitoring functionality."""
    
    def test_memory_monitor_initialization(self):
        """Test memory monitor initialization."""
        monitor = MemoryMonitor(check_interval=1.0)
        
        assert monitor.check_interval == 1.0
        assert not monitor._monitoring
        assert monitor._monitor_thread is None
        assert len(monitor._callbacks) == 0
    
    @patch('src.core.memory_manager.psutil.virtual_memory')
    @patch('src.core.memory_manager.psutil.swap_memory')
    def test_get_current_metrics(self, mock_swap, mock_memory):
        """Test getting current memory metrics."""
        # Mock memory data
        mock_memory.return_value = Mock(
            total=16 * 1024**3,  # 16GB
            available=8 * 1024**3,  # 8GB
            used=8 * 1024**3,  # 8GB
            percent=50.0
        )
        mock_swap.return_value = Mock(used=0, percent=0.0)
        
        monitor = MemoryMonitor()
        metrics = monitor.get_current_metrics()
        
        assert metrics.total_memory == 16 * 1024**3
        assert metrics.available_memory == 8 * 1024**3
        assert metrics.memory_percent == 50.0
        assert metrics.pressure_level == MemoryPressureLevel.LOW
    
    @patch('src.core.memory_manager.psutil.virtual_memory')
    @patch('src.core.memory_manager.psutil.swap_memory')
    def test_pressure_level_detection(self, mock_swap, mock_memory):
        """Test memory pressure level detection."""
        mock_swap.return_value = Mock(used=0, percent=0.0)
        monitor = MemoryMonitor()
        
        # Test different pressure levels
        test_cases = [
            (60.0, MemoryPressureLevel.LOW),
            (75.0, MemoryPressureLevel.MODERATE),
            (85.0, MemoryPressureLevel.HIGH),
            (95.0, MemoryPressureLevel.CRITICAL)
        ]
        
        for memory_percent, expected_level in test_cases:
            mock_memory.return_value = Mock(
                total=16 * 1024**3,
                available=8 * 1024**3,
                used=8 * 1024**3,
                percent=memory_percent
            )
            
            metrics = monitor.get_current_metrics()
            assert metrics.pressure_level == expected_level
    
    def test_callback_management(self):
        """Test callback registration and removal."""
        monitor = MemoryMonitor()
        callback1 = Mock()
        callback2 = Mock()
        
        # Add callbacks
        monitor.add_callback(callback1)
        monitor.add_callback(callback2)
        assert len(monitor._callbacks) == 2
        
        # Remove callback
        monitor.remove_callback(callback1)
        assert len(monitor._callbacks) == 1
        assert callback2 in monitor._callbacks
    
    @patch('src.core.memory_manager.psutil.virtual_memory')
    @patch('src.core.memory_manager.psutil.swap_memory')
    def test_monitoring_lifecycle(self, mock_swap, mock_memory):
        """Test monitoring start/stop lifecycle."""
        mock_memory.return_value = Mock(
            total=16 * 1024**3, available=8 * 1024**3,
            used=8 * 1024**3, percent=50.0
        )
        mock_swap.return_value = Mock(used=0, percent=0.0)
        
        monitor = MemoryMonitor(check_interval=0.1)
        callback = Mock()
        monitor.add_callback(callback)
        
        # Start monitoring
        monitor.start_monitoring()
        assert monitor._monitoring
        assert monitor._monitor_thread is not None
        
        # Wait for at least one callback
        time.sleep(0.2)
        
        # Stop monitoring
        monitor.stop_monitoring()
        assert not monitor._monitoring
        
        # Verify callback was called
        assert callback.call_count > 0


class TestResourceTracker:
    """Test resource tracking functionality."""
    
    def test_resource_registration(self):
        """Test resource registration."""
        tracker = ResourceTracker()
        resource = Mock()
        
        tracker.register_resource("test_component", "resource_1", resource, 1024)
        
        usage = tracker.get_component_usage("test_component")
        assert usage['total_size'] == 1024
        assert usage['resource_count'] == 1
        assert 'resource_1' in usage['resources']
    
    def test_access_time_update(self):
        """Test access time updates."""
        tracker = ResourceTracker()
        resource = Mock()
        
        tracker.register_resource("test_component", "resource_1", resource, 1024)
        
        # Get initial access time
        usage = tracker.get_component_usage("test_component")
        initial_time = usage['resources']['resource_1']['last_accessed']
        
        # Wait a bit and update access time
        time.sleep(0.01)
        tracker.update_access_time("test_component", "resource_1")
        
        # Verify access time was updated
        usage = tracker.get_component_usage("test_component")
        updated_time = usage['resources']['resource_1']['last_accessed']
        assert updated_time > initial_time
    
    def test_total_usage_calculation(self):
        """Test total usage calculation across components."""
        tracker = ResourceTracker()
        
        # Keep references to prevent garbage collection
        resource1 = Mock()
        resource2 = Mock()
        resource3 = Mock()
        
        # Register resources in different components
        tracker.register_resource("component_1", "resource_1", resource1, 1024)
        tracker.register_resource("component_1", "resource_2", resource2, 2048)
        tracker.register_resource("component_2", "resource_3", resource3, 512)
        
        total_usage = tracker.get_total_usage()
        
        assert total_usage['total_size'] == 3584  # 1024 + 2048 + 512
        assert total_usage['total_count'] == 3
        assert len(total_usage['components']) == 2
        assert total_usage['components']['component_1']['size_bytes'] == 3072
        assert total_usage['components']['component_2']['size_bytes'] == 512
    
    def test_stale_resource_detection(self):
        """Test detection of stale resources."""
        tracker = ResourceTracker()
        resource = Mock()
        
        tracker.register_resource("test_component", "resource_1", resource, 1024)
        
        # Resource should not be stale immediately
        stale = tracker.find_stale_resources(timedelta(minutes=1))
        assert len(stale) == 0
        
        # Mock old access time
        with tracker._lock:
            old_time = datetime.now() - timedelta(minutes=2)
            tracker._resources["test_component"]["resource_1"]["last_accessed"] = old_time
        
        # Now resource should be stale
        stale = tracker.find_stale_resources(timedelta(minutes=1))
        assert len(stale) == 1
        assert stale[0] == ("test_component", "resource_1")


class TestMemoryOptimizer:
    """Test memory optimization functionality."""
    
    def test_optimization_callback_registration(self):
        """Test optimization callback registration."""
        tracker = ResourceTracker()
        optimizer = MemoryOptimizer(tracker)
        
        callback1 = Mock(return_value=1024)
        callback2 = Mock(return_value=2048)
        
        optimizer.register_optimization_callback(callback1)
        optimizer.register_optimization_callback(callback2)
        
        assert len(optimizer._optimization_callbacks) == 2
    
    @patch('src.core.memory_manager.psutil.virtual_memory')
    @patch('src.core.memory_manager.psutil.Process')
    @patch('src.core.memory_manager.gc.collect')
    def test_memory_optimization(self, mock_gc, mock_process, mock_memory):
        """Test memory optimization process."""
        # Mock memory data
        mock_memory.side_effect = [
            Mock(available=500 * 1024 * 1024),  # Start: 500MB available
            Mock(available=600 * 1024 * 1024)   # End: 600MB available
        ]
        
        # Mock process memory to show memory freed by GC
        mock_process_instance = Mock()
        # First call (before GC): 1GB, Second call (after GC): 950MB (50MB freed)
        mock_process_instance.memory_info.side_effect = [
            Mock(rss=1024 * 1024 * 1024),      # 1GB before GC
            Mock(rss=974 * 1024 * 1024)        # 950MB after GC (50MB freed)
        ]
        mock_process.return_value = mock_process_instance
        
        # Mock garbage collection
        mock_gc.return_value = 100  # 100 objects collected
        
        tracker = ResourceTracker()
        optimizer = MemoryOptimizer(tracker)
        
        # Add optimization callback
        callback = Mock(return_value=50 * 1024 * 1024)  # Returns 50MB freed
        optimizer.register_optimization_callback(callback)
        
        # Run optimization
        result = optimizer.optimize_memory(target_free_mb=100)
        
        assert result['target_free_mb'] == 100
        assert 'garbage_collection' in result['strategies_used']
        assert result['bytes_freed'] > 0
        
        # Verify callback was called
        callback.assert_called_once()
    
    @patch('src.core.memory_manager.gc.collect')
    def test_garbage_collection_strategy(self, mock_gc):
        """Test garbage collection strategy."""
        mock_gc.return_value = 50  # 50 objects collected
        
        tracker = ResourceTracker()
        optimizer = MemoryOptimizer(tracker)
        
        freed = optimizer._run_garbage_collection()
        
        # Should have called gc.collect for each generation
        assert mock_gc.call_count == 3
        assert freed >= 0  # Should return non-negative value


class TestMemoryManager:
    """Test main memory manager functionality."""
    
    @patch('src.core.memory_manager.psutil.virtual_memory')
    def test_memory_manager_initialization(self, mock_memory):
        """Test memory manager initialization."""
        mock_memory.return_value = Mock(total=8 * 1024**3)  # 8GB
        
        manager = MemoryManager()
        
        assert manager.monitor is not None
        assert manager.resource_tracker is not None
        assert manager.optimizer is not None
        assert manager._allocation_config is not None
    
    @patch('src.core.memory_manager.psutil.virtual_memory')
    def test_resource_allocation_configuration(self, mock_memory):
        """Test resource allocation configuration."""
        mock_memory.return_value = Mock(total=16 * 1024**3)  # 16GB
        
        manager = MemoryManager()
        
        # Test default allocation for 16GB system
        config = manager._allocation_config
        assert config.max_cache_memory_mb == 2048
        assert config.max_model_memory_mb == 4096
        assert config.max_document_memory_mb == 1024
        
        # Test custom configuration
        custom_config = ResourceAllocation(
            max_cache_memory_mb=1024,
            max_model_memory_mb=2048,
            max_document_memory_mb=512,
            gc_threshold_mb=256,
            cleanup_threshold_mb=512
        )
        
        manager.configure_allocation(custom_config)
        assert manager._allocation_config == custom_config
    
    def test_resource_registration(self):
        """Test resource registration through manager."""
        manager = MemoryManager()
        resource = Mock()
        
        manager.register_resource("test_component", "resource_1", resource, 1024)
        
        # Verify resource was registered
        usage = manager.resource_tracker.get_component_usage("test_component")
        assert usage['total_size'] == 1024
        assert usage['resource_count'] == 1
    
    @patch('src.core.memory_manager.psutil.virtual_memory')
    def test_memory_status_reporting(self, mock_memory):
        """Test memory status reporting."""
        mock_memory.return_value = Mock(
            total=16 * 1024**3,
            available=8 * 1024**3,
            percent=50.0
        )
        
        manager = MemoryManager()
        # Keep reference to prevent garbage collection
        test_resource = Mock()
        manager.register_resource("test_component", "resource_1", test_resource, 1024 * 1024)
        
        status = manager.get_memory_status()
        
        assert 'system_memory' in status
        assert 'resource_usage' in status
        assert 'allocation_config' in status
        
        assert status['system_memory']['total_mb'] == 16 * 1024
        assert status['system_memory']['available_mb'] == 8 * 1024
        assert status['resource_usage']['total_size_mb'] == 1
    
    @patch('src.core.memory_manager.psutil.virtual_memory')
    def test_pressure_based_optimization(self, mock_memory):
        """Test optimization based on memory pressure."""
        manager = MemoryManager()
        
        # Mock high memory pressure
        high_pressure_metrics = Mock(
            pressure_level=MemoryPressureLevel.HIGH,
            memory_percent=85.0
        )
        
        with patch.object(manager.monitor, 'get_current_metrics', 
                         return_value=high_pressure_metrics):
            with patch.object(manager.optimizer, 'optimize_memory', 
                             return_value={'success': True}) as mock_optimize:
                
                result = manager.optimize_if_needed()
                
                # Should have triggered optimization
                assert result is not None
                mock_optimize.assert_called_once()
    
    def test_lifecycle_management(self):
        """Test manager lifecycle (start/stop)."""
        manager = MemoryManager()
        
        # Start manager
        manager.start()
        assert manager.monitor._monitoring
        
        # Stop manager
        manager.stop()
        assert not manager.monitor._monitoring


class TestIntegration:
    """Integration tests for memory management components."""
    
    @patch('src.core.memory_manager.psutil.virtual_memory')
    @patch('src.core.memory_manager.psutil.swap_memory')
    def test_end_to_end_memory_management(self, mock_swap, mock_memory):
        """Test end-to-end memory management workflow."""
        # Mock system memory
        mock_memory.return_value = Mock(
            total=8 * 1024**3,
            available=2 * 1024**3,  # Low available memory
            used=6 * 1024**3,
            percent=75.0
        )
        mock_swap.return_value = Mock(used=0, percent=0.0)
        
        manager = MemoryManager()
        
        # Register some resources
        resources = [Mock() for _ in range(5)]
        for i, resource in enumerate(resources):
            manager.register_resource(f"component_{i}", f"resource_{i}", 
                                    resource, 100 * 1024 * 1024)  # 100MB each
        
        # Get initial status
        initial_status = manager.get_memory_status()
        assert initial_status['resource_usage']['total_size_mb'] == 500
        
        # Test optimization
        with patch.object(manager.optimizer, 'optimize_memory', 
                         return_value={'success': True, 'bytes_freed': 200 * 1024 * 1024}):
            result = manager.optimize_if_needed(force=True)
            assert result is not None
            assert result['success']
    
    def test_memory_pressure_callback_chain(self):
        """Test memory pressure callback chain."""
        manager = MemoryManager()
        optimization_called = threading.Event()
        
        # Mock optimizer to signal when called
        # Store reference to original method
        _ = manager.optimizer.optimize_memory
        def mock_optimize(*args, **kwargs):
            optimization_called.set()
            return {'success': True, 'bytes_freed': 100 * 1024 * 1024}
        
        manager.optimizer.optimize_memory = mock_optimize
        
        # Simulate critical memory pressure
        critical_metrics = Mock(
            pressure_level=MemoryPressureLevel.CRITICAL,
            memory_percent=95.0,
            total_memory=8 * 1024**3,
            available_memory=400 * 1024**2,  # 400MB
            used_memory=7.6 * 1024**3,
            swap_used=0,
            swap_percent=0.0,
            timestamp=datetime.now()
        )
        
        # Trigger pressure callback
        manager._handle_memory_pressure(critical_metrics)
        
        # Wait for optimization to be triggered
        assert optimization_called.wait(timeout=1.0), "Optimization should have been triggered"


if __name__ == "__main__":
    pytest.main([__file__])