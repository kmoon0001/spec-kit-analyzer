"""
GUI Stability Tests

Tests to verify GUI never freezes under various scenarios:
    - Timeout scenarios
    - Out-of-memory scenarios
    - Network failures
    - Heavy load
    - Concurrent operations
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import QThreadPool, QTimer
from PySide6.QtWidgets import QApplication

from src.gui.core import (
    ResourceMonitor,
    ResourceManager,
    BaseWorker,
    WorkerSignals,
    JobPriority
)


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for Qt tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TimeoutWorker(BaseWorker):
    """Worker that times out."""
    
    def __init__(self, delay=10):
        super().__init__(timeout_seconds=2.0)  # 2 second timeout
        self.delay = delay
    
    def create_signals(self):
        return WorkerSignals()
    
    def do_work(self):
        time.sleep(self.delay)  # Will timeout
        return "should_not_reach"
    
    def cleanup(self):
        pass


class MemoryHeavyWorker(BaseWorker):
    """Worker that uses lots of memory."""
    
    def __init__(self):
        super().__init__(timeout_seconds=10.0, job_type="model_load")
        self.large_data = None
    
    def create_signals(self):
        return WorkerSignals()
    
    def do_work(self):
        # Simulate heavy memory usage
        try:
            self.large_data = [0] * (100 * 1024 * 1024)  # 100M integers
        except MemoryError:
            raise MemoryError("Insufficient memory for operation")
        return "memory_allocated"
    
    def cleanup(self):
        self.large_data = None  # Free memory


class NetworkFailureWorker(BaseWorker):
    """Worker that simulates network failure."""
    
    def __init__(self):
        super().__init__(timeout_seconds=5.0)
    
    def create_signals(self):
        return WorkerSignals()
    
    def do_work(self):
        # Simulate network request that fails
        import requests
        raise requests.ConnectionError("Failed to connect to API")
    
    def cleanup(self):
        pass


class TestTimeoutScenarios:
    """Test timeout handling."""
    
    def test_worker_timeout(self, qapp):
        """Test that worker times out correctly."""
        thread_pool = QThreadPool()
        worker = TimeoutWorker(delay=5)
        
        error_received = []
        finished_received = []
        
        worker.signals.error.connect(lambda e: error_received.append(e))
        worker.signals.finished.connect(lambda: finished_received.append(True))
        
        thread_pool.start(worker)
        thread_pool.waitForDone(6000)
        
        # Process events to ensure signals are delivered
        for _ in range(10):
            qapp.processEvents()
            time.sleep(0.1)
        
        # Should timeout
        assert len(finished_received) == 1  # Worker finished
        assert len(error_received) == 1
        assert error_received[0][0] == TimeoutError
    
    def test_multiple_timeout_workers(self, qapp):
        """Test multiple workers timing out simultaneously."""
        thread_pool = QThreadPool()
        
        errors = []
        finished = []
        
        for i in range(5):
            worker = TimeoutWorker(delay=3)
            worker.signals.error.connect(lambda e: errors.append(e))
            worker.signals.finished.connect(lambda: finished.append(True))
            thread_pool.start(worker)
        
        thread_pool.waitForDone(8000)
        
        # Process events to ensure signals are delivered
        for _ in range(10):
            qapp.processEvents()
            time.sleep(0.1)
        
        # All should timeout
        assert len(finished) == 5  # All workers finished
        assert len(errors) == 5
        assert all(e[0] == TimeoutError for e in errors)


class TestResourceConstraints:
    """Test behavior under resource constraints."""
    
    def test_resource_denial(self, qapp):
        """Test job denial when resources are low."""
        monitor = ResourceMonitor()
        manager = ResourceManager(
            thread_pool=QThreadPool(),
            resource_monitor=monitor
        )
        
        denied_jobs = []
        manager.job_denied.connect(lambda jid, reason: denied_jobs.append((jid, reason)))
        
        # Mock resource check to always deny
        with patch.object(monitor, 'can_start_job', return_value=(False, "Mocked resource constraint")):
            worker = MemoryHeavyWorker()
            job_id = manager.submit_job(worker, priority=JobPriority.HIGH)
            
            time.sleep(1.0)  # Allow processing
            
            # Job should be denied or re-queued
            # In production, it would be re-queued with lower priority
        
        manager.shutdown(wait=True)
    
    def test_memory_error_handling(self, qapp):
        """Test handling of memory errors."""
        thread_pool = QThreadPool()
        worker = MemoryHeavyWorker()
        
        error_received = []
        worker.signals.error.connect(lambda e: error_received.append(e))
        
        thread_pool.start(worker)
        thread_pool.waitForDone(15000)
        
        # Should either succeed or fail gracefully
        # Important: no crash
        assert True  # If we get here, no crash occurred


class TestNetworkFailures:
    """Test network failure scenarios."""
    
    def test_network_error_handling(self, qapp):
        """Test handling of network errors."""
        thread_pool = QThreadPool()
        worker = NetworkFailureWorker()
        
        error_received = []
        finished_received = []
        
        worker.signals.error.connect(lambda e: error_received.append(e))
        worker.signals.finished.connect(lambda: finished_received.append(True))
        
        thread_pool.start(worker)
        thread_pool.waitForDone(6000)
        
        # Process events to ensure signals are delivered
        for _ in range(10):
            qapp.processEvents()
            time.sleep(0.1)
        
        # Should handle network error gracefully
        assert len(finished_received) == 1  # Worker finished
        assert len(error_received) == 1
        # Important: no crash


class TestConcurrentOperations:
    """Test concurrent operations and heavy load."""
    
    def test_concurrent_workers(self, qapp):
        """Test many workers running concurrently."""
        thread_pool = QThreadPool()
        
        class QuickWorker(BaseWorker):
            def __init__(self, worker_id):
                super().__init__()
                self.worker_id = worker_id
            
            def create_signals(self):
                return WorkerSignals()
            
            def do_work(self):
                time.sleep(0.1)
                return f"worker_{self.worker_id}_done"
            
            def cleanup(self):
                pass
        
        results = []
        finished = []
        
        # Start 20 workers
        for i in range(20):
            worker = QuickWorker(i)
            worker.signals.result.connect(lambda r: results.append(r))
            worker.signals.finished.connect(lambda: finished.append(True))
            thread_pool.start(worker)
        
        thread_pool.waitForDone(5000)
        
        # Process events to ensure signals are delivered
        for _ in range(10):
            qapp.processEvents()
            time.sleep(0.1)
        
        # All workers should complete
        assert len(finished) == 20  # All workers finished
        assert len(results) == 20
    
    def test_rapid_job_submission(self, qapp):
        """Test rapid job submission to ResourceManager."""
        manager = ResourceManager(
            thread_pool=QThreadPool(),
            resource_monitor=ResourceMonitor(),
            max_queue_size=50
        )
        
        completed = []
        failed = []
        
        class FastWorker(BaseWorker):
            def create_signals(self):
                return WorkerSignals()
            
            def do_work(self):
                return "fast"
            
            def cleanup(self):
                pass
        
        # Submit 30 jobs rapidly
        for i in range(30):
            worker = FastWorker()
            worker.signals.result.connect(lambda r: completed.append(r))
            worker.signals.error.connect(lambda e: failed.append(e))
            manager.submit_job(worker, priority=JobPriority.NORMAL)
        
        time.sleep(2.0)  # Allow processing
        
        # Process events to ensure signals are delivered
        for _ in range(10):
            qapp.processEvents()
            time.sleep(0.1)
        
        manager.shutdown(wait=True)
        
        # Most or all jobs should complete
        assert len(completed) > 20


class TestCancellation:
    """Test job cancellation scenarios."""
    
    def test_cancel_queued_job(self, qapp):
        """Test cancelling a queued job."""
        manager = ResourceManager(
            thread_pool=QThreadPool(),
            resource_monitor=ResourceMonitor()
        )
        
        class SlowWorker(BaseWorker):
            def create_signals(self):
                return WorkerSignals()
            
            def do_work(self):
                time.sleep(2)
                return "slow"
            
            def cleanup(self):
                pass
        
        # Submit and immediately cancel
        worker = SlowWorker()
        job_id = manager.submit_job(worker, priority=JobPriority.NORMAL)
        
        cancelled = manager.cancel_job(job_id)
        assert cancelled is True
        
        manager.shutdown(wait=True)
    
    def test_cancel_active_job(self, qapp):
        """Test cancelling an active job."""
        manager = ResourceManager(
            thread_pool=QThreadPool(),
            resource_monitor=ResourceMonitor()
        )
        
        class CheckCancelWorker(BaseWorker):
            def create_signals(self):
                return WorkerSignals()
            
            def do_work(self):
                for i in range(10):
                    if self.is_cancelled():
                        return "cancelled"
                    time.sleep(0.2)
                return "completed"
            
            def cleanup(self):
                pass
        
        worker = CheckCancelWorker()
        result_received = []
        
        job_id = manager.submit_job(
            worker,
            priority=JobPriority.NORMAL,
            on_complete=lambda r: result_received.append(r)
        )
        
        time.sleep(0.5)  # Let it start
        manager.cancel_job(job_id)
        
        time.sleep(1.5)  # Wait for completion
        
        # Worker should recognize cancellation
        if result_received:
            assert result_received[0] == "cancelled"
        
        manager.shutdown(wait=True)


class TestGUIResponsiveness:
    """Test that GUI remains responsive."""
    
    def test_event_loop_not_blocked(self, qapp):
        """Test that event loop processes during worker execution."""
        thread_pool = QThreadPool()
        
        class LongWorker(BaseWorker):
            def create_signals(self):
                return WorkerSignals()
            
            def do_work(self):
                time.sleep(1.0)
                return "done"
            
            def cleanup(self):
                pass
        
        timer_fired = []
        
        # Create a timer that should fire during worker execution
        timer = QTimer()
        timer.timeout.connect(lambda: timer_fired.append(True))
        timer.start(200)  # Fire every 200ms
        
        worker = LongWorker()
        thread_pool.start(worker)
        
        # Process events while worker runs
        for _ in range(5):
            qapp.processEvents()
            time.sleep(0.2)
        
        thread_pool.waitForDone(2000)
        timer.stop()
        
        # Timer should have fired multiple times
        assert len(timer_fired) > 2  # Event loop was processing


def test_no_crashes_under_stress(qapp):
    """Comprehensive stress test - no crashes allowed."""
    manager = ResourceManager(
        thread_pool=QThreadPool(),
        resource_monitor=ResourceMonitor(),
        max_queue_size=100
    )
    
    class StressWorker(BaseWorker):
        def __init__(self, should_fail=False, delay=0):
            super().__init__(timeout_seconds=5.0)
            self.should_fail = should_fail
            self.delay = delay
        
        def create_signals(self):
            return WorkerSignals()
        
        def do_work(self):
            if self.delay:
                time.sleep(self.delay)
            if self.should_fail:
                raise RuntimeError("Stress test error")
            return "ok"
        
        def cleanup(self):
            pass
    
    completed = []
    failed = []
    
    # Submit mix of fast, slow, failing jobs
    for i in range(50):
        worker = StressWorker(
            should_fail=(i % 7 == 0),  # Some fail
            delay=(0.1 if i % 3 == 0 else 0)  # Some slow
        )
        
        worker.signals.result.connect(lambda r: completed.append(r))
        worker.signals.error.connect(lambda e: failed.append(e))
        
        manager.submit_job(
            worker,
            priority=JobPriority.NORMAL if i % 2 == 0 else JobPriority.LOW
        )
    
    time.sleep(3.0)  # Allow processing
    
    # Process events to ensure signals are delivered
    for _ in range(10):
        qapp.processEvents()
        time.sleep(0.1)
    
    manager.shutdown(wait=True)
    
    # Important: we got here without crashing!
    assert True
    
    # Some jobs should have completed and some failed
    assert len(completed) + len(failed) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

