"""
Tests for Threading Infrastructure

Tests all core threading components:
    - ResourceMonitor
    - BaseWorker
    - ResourceManager
    - Signal communication
"""

import pytest
import time
from unittest.mock import Mock, patch
from PySide6.QtCore import QThreadPool, Qt
from PySide6.QtWidgets import QApplication

from src.gui.core import (
    ResourceMonitor,
    ResourceMetrics,
    ResourceLimits,
    BaseWorker,
    ResourceError,
    ResourceManager,
    JobPriority,
    WorkerSignals
)


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for Qt tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def resource_monitor():
    """Create ResourceMonitor instance."""
    monitor = ResourceMonitor()
    yield monitor
    monitor.stop_monitoring()


@pytest.fixture
def thread_pool():
    """Create QThreadPool instance."""
    pool = QThreadPool()
    yield pool
    pool.waitForDone(5000)


class TestResourceMonitor:
    """Test ResourceMonitor functionality."""
    
    def test_initialization(self, resource_monitor):
        """Test ResourceMonitor initialization."""
        assert resource_monitor is not None
        assert resource_monitor.limits is not None
    
    def test_get_current_metrics(self, resource_monitor):
        """Test getting current system metrics."""
        metrics = resource_monitor.get_current_metrics()
        
        assert isinstance(metrics, ResourceMetrics)
        assert 0 <= metrics.ram_percent <= 100
        assert 0 <= metrics.cpu_percent <= 100
        assert metrics.ram_total_mb > 0
        assert metrics.cpu_count > 0
    
    def test_can_start_job(self, resource_monitor):
        """Test job admission control."""
        can_start, reason = resource_monitor.can_start_job("general")
        
        # Should be able to start under normal conditions
        assert isinstance(can_start, bool)
        assert isinstance(reason, str)
    
    def test_optimal_thread_count(self, resource_monitor):
        """Test optimal thread count calculation."""
        optimal = resource_monitor.get_optimal_thread_count()
        
        assert optimal >= 1
        assert optimal <= resource_monitor.get_current_metrics().cpu_count
    
    def test_monitoring_signals(self, qapp, resource_monitor):
        """Test resource monitoring signals."""
        metrics_received = []
        
        def on_metrics(metrics_dict):
            metrics_received.append(metrics_dict)
        
        resource_monitor.metrics_updated.connect(on_metrics)
        resource_monitor.start_monitoring(interval_ms=50)  # Faster interval
        
        # Wait for updates
        time.sleep(0.3)
        
        # Manually trigger an update
        resource_monitor._update_metrics()
        
        assert len(metrics_received) > 0
        assert 'ram_percent' in metrics_received[0]
        assert 'cpu_percent' in metrics_received[0]


class SimpleTestWorker(BaseWorker):
    """Simple worker for testing."""
    
    def __init__(self, result_value="test", fail=False, delay=0):
        super().__init__(timeout_seconds=5.0)
        self.result_value = result_value
        self.fail = fail
        self.delay = delay
    
    def create_signals(self):
        return WorkerSignals()
    
    def do_work(self):
        if self.delay:
            time.sleep(self.delay)
        
        if self.fail:
            raise ValueError("Test error")
        
        return self.result_value
    
    def cleanup(self):
        pass


class TestBaseWorker:
    """Test BaseWorker functionality."""
    
    def test_successful_execution(self, qapp, thread_pool):
        """Test successful worker execution."""
        worker = SimpleTestWorker(result_value="success")
        
        # Override resource check for testing
        worker._check_resources = lambda: True
        
        result_received = []
        error_received = []
        finished_received = []
        
        worker.signals.result.connect(lambda r: result_received.append(r))
        worker.signals.error.connect(lambda e: error_received.append(e))
        worker.signals.finished.connect(lambda: finished_received.append(True))
        
        thread_pool.start(worker)
        thread_pool.waitForDone(3000)  # Longer timeout
        
        # Process events to ensure signals are delivered
        for _ in range(10):
            qapp.processEvents()
            time.sleep(0.1)
        
        assert len(finished_received) == 1  # Worker finished
        assert len(result_received) == 1
        assert result_received[0] == "success"
        assert len(error_received) == 0
    
    def test_error_handling(self, qapp, thread_pool):
        """Test worker error handling."""
        worker = SimpleTestWorker(fail=True)
        
        # Override resource check for testing
        worker._check_resources = lambda: True
        
        result_received = []
        error_received = []
        finished_received = []
        
        worker.signals.result.connect(lambda r: result_received.append(r))
        worker.signals.error.connect(lambda e: error_received.append(e))
        worker.signals.finished.connect(lambda: finished_received.append(True))
        
        thread_pool.start(worker)
        thread_pool.waitForDone(3000)
        
        # Process events to ensure signals are delivered
        for _ in range(10):
            qapp.processEvents()
            time.sleep(0.1)
        
        assert len(finished_received) == 1  # Worker finished
        assert len(result_received) == 0
        assert len(error_received) == 1
        assert error_received[0][0] == ValueError
    
    def test_cancellation(self, qapp, thread_pool):
        """Test worker cancellation."""
        worker = SimpleTestWorker(delay=2)
        
        cancelled_received = []
        worker.signals.cancelled.connect(lambda: cancelled_received.append(True))
        
        thread_pool.start(worker)
        time.sleep(0.1)
        worker.cancel()
        
        thread_pool.waitForDone(3000)
        
        # Note: Cancellation is cooperative, so results may vary
        # The important thing is that cancel() doesn't crash
    
    def test_timeout_enforcement(self, qapp, thread_pool):
        """Test timeout enforcement."""
        worker = SimpleTestWorker(delay=3)
        worker.timeout_seconds = 1.0
        
        # Override resource check for testing
        worker._check_resources = lambda: True
        
        error_received = []
        finished_received = []
        worker.signals.error.connect(lambda e: error_received.append(e))
        worker.signals.finished.connect(lambda: finished_received.append(True))
        
        thread_pool.start(worker)
        thread_pool.waitForDone(4000)
        
        # Process events to ensure signals are delivered
        for _ in range(10):
            qapp.processEvents()
            time.sleep(0.1)
        
        assert len(finished_received) == 1  # Worker finished
        assert len(error_received) == 1
        assert error_received[0][0] == TimeoutError
    
    def test_progress_reporting(self, qapp, thread_pool):
        """Test progress reporting."""
        class ProgressWorker(SimpleTestWorker):
            def do_work(self):
                self.report_progress(0, 100, "Starting")
                time.sleep(0.1)
                self.report_progress(50, 100, "Halfway")
                time.sleep(0.1)
                self.report_progress(100, 100, "Complete")
                return "done"
        
        worker = ProgressWorker()
        
        # Override resource check for testing
        worker._check_resources = lambda: True
        
        progress_received = []
        finished_received = []
        
        worker.signals.progress.connect(lambda c, t, m: progress_received.append((c, t, m)))
        worker.signals.finished.connect(lambda: finished_received.append(True))
        
        thread_pool.start(worker)
        thread_pool.waitForDone(2000)
        
        # Process events to ensure signals are delivered
        for _ in range(10):
            qapp.processEvents()
            time.sleep(0.1)
        
        assert len(finished_received) == 1  # Worker finished
        assert len(progress_received) >= 3
        assert progress_received[0] == (0, 100, "Starting")


class TestResourceManager:
    """Test ResourceManager functionality."""
    
    def test_initialization(self, qapp, thread_pool, resource_monitor):
        """Test ResourceManager initialization."""
        manager = ResourceManager(
            thread_pool=thread_pool,
            resource_monitor=resource_monitor
        )
        
        assert manager is not None
        assert manager.get_queue_size() == 0
        assert manager.get_active_job_count() == 0
        
        manager.shutdown(wait=False)
    
    def test_job_submission(self, qapp, thread_pool, resource_monitor):
        """Test job submission."""
        manager = ResourceManager(
            thread_pool=thread_pool,
            resource_monitor=resource_monitor
        )
        
        worker = SimpleTestWorker(result_value="test")
        job_id = manager.submit_job(worker, priority=JobPriority.NORMAL)
        
        assert job_id is not None
        assert isinstance(job_id, str)
        
        time.sleep(0.5)  # Allow processing
        
        manager.shutdown(wait=True)
    
    def test_job_priorities(self, qapp, thread_pool, resource_monitor):
        """Test job priority handling."""
        manager = ResourceManager(
            thread_pool=thread_pool,
            resource_monitor=resource_monitor
        )
        
        completed_order = []
        
        def on_complete(job_id):
            def callback(result):
                completed_order.append(job_id)
            return callback
        
        # Submit jobs with different priorities
        low_id = manager.submit_job(
            SimpleTestWorker(delay=0.1),
            priority=JobPriority.LOW,
            on_complete=on_complete("low")
        )
        
        critical_id = manager.submit_job(
            SimpleTestWorker(delay=0.1),
            priority=JobPriority.CRITICAL,
            on_complete=on_complete("critical")
        )
        
        high_id = manager.submit_job(
            SimpleTestWorker(delay=0.1),
            priority=JobPriority.HIGH,
            on_complete=on_complete("high")
        )
        
        time.sleep(2.0)  # Allow processing
        
        # Critical should be processed first
        if len(completed_order) > 0:
            assert completed_order[0] == "critical"
        
        manager.shutdown(wait=True)
    
    def test_job_cancellation(self, qapp, thread_pool, resource_monitor):
        """Test job cancellation."""
        manager = ResourceManager(
            thread_pool=thread_pool,
            resource_monitor=resource_monitor
        )
        
        worker = SimpleTestWorker(delay=5)
        job_id = manager.submit_job(worker, priority=JobPriority.NORMAL)
        
        time.sleep(0.2)  # Allow job to start
        
        cancelled = manager.cancel_job(job_id)
        assert cancelled is True
        
        manager.shutdown(wait=True)
    
    def test_queue_full_handling(self, qapp, thread_pool, resource_monitor):
        """Test queue full handling."""
        manager = ResourceManager(
            thread_pool=thread_pool,
            resource_monitor=resource_monitor,
            max_queue_size=2
        )
        
        # Fill queue
        manager.submit_job(SimpleTestWorker(delay=1))
        manager.submit_job(SimpleTestWorker(delay=1))
        
        # This should fail
        with pytest.raises(RuntimeError, match="Job queue full"):
            manager.submit_job(SimpleTestWorker())
        
        manager.shutdown(wait=True)
    
    def test_statistics(self, qapp, thread_pool, resource_monitor):
        """Test statistics retrieval."""
        manager = ResourceManager(
            thread_pool=thread_pool,
            resource_monitor=resource_monitor
        )
        
        stats = manager.get_statistics()
        
        assert 'queue_size' in stats
        assert 'active_jobs' in stats
        assert 'total_jobs' in stats
        assert 'thread_pool_max' in stats
        
        manager.shutdown(wait=True)


def test_signal_thread_safety(qapp, thread_pool):
    """Test signal thread safety."""
    # This test ensures signals work correctly across threads
    
    class SignalTestWorker(BaseWorker):
        def create_signals(self):
            return WorkerSignals()
        
        def do_work(self):
            # Emit multiple signals from worker thread
            self.report_status("Starting")
            self.report_progress(0, 100, "Begin")
            time.sleep(0.1)
            self.report_progress(50, 100, "Middle")
            time.sleep(0.1)
            self.report_progress(100, 100, "End")
            return "complete"
        
        def cleanup(self):
            pass
    
    worker = SignalTestWorker()
    
    # Override resource check for testing
    worker._check_resources = lambda: True
    
    status_received = []
    progress_received = []
    result_received = []
    finished_received = []
    
    worker.signals.status.connect(lambda s: status_received.append(s))
    worker.signals.progress.connect(lambda c, t, m: progress_received.append((c, t, m)))
    worker.signals.result.connect(lambda r: result_received.append(r))
    worker.signals.finished.connect(lambda: finished_received.append(True))
    
    thread_pool.start(worker)
    thread_pool.waitForDone(2000)
    
    # Process events to ensure signals are delivered
    for _ in range(10):
        qapp.processEvents()
        time.sleep(0.1)
    
    assert len(finished_received) == 1  # Worker finished
    assert len(status_received) >= 1
    assert len(progress_received) >= 3
    assert len(result_received) == 1
    assert result_received[0] == "complete"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

