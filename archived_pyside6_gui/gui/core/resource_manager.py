"""
Resource Manager with Job Queue and Graceful Degradation

Manages system resources and job execution with:
    - Priority-based job queue
    - Graceful degradation under load
    - Automatic job scheduling
    - Resource allocation strategy
    - Job cancellation and cleanup

Architecture:
    - Uses ResourceMonitor for metrics
    - Manages QThreadPool workers
    - Implements priority queue
    - Handles job lifecycle
"""

import logging
from typing import Any
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from queue import PriorityQueue
from PySide6.QtCore import QObject, Signal, QTimer, QThreadPool

from .resource_monitor import ResourceMonitor
from .base_worker import BaseWorker


logger = logging.getLogger(__name__)


class JobPriority(IntEnum):
    """Job priority levels (lower number = higher priority)."""

    CRITICAL = 0  # User-initiated, interactive tasks
    HIGH = 1  # Important background tasks
    NORMAL = 2  # Standard tasks
    LOW = 3  # Deferred/batch tasks


@dataclass(order=True)
class Job:
    """
    Represents a job to be executed.

    Jobs are ordered by priority (lower number = higher priority).
    """

    priority: int
    worker: BaseWorker = field(compare=False)
    callback: Callable[[Any], None] | None = field(default=None, compare=False)
    error_callback: Callable[[tuple], None] | None = field(default=None, compare=False)
    job_id: str = field(default_factory=lambda: f"job_{datetime.now().timestamp()}", compare=False)
    created_at: datetime = field(default_factory=datetime.now, compare=False)
    job_type: str = field(default="general", compare=False)


class ResourceManager(QObject):
    """
    Manages system resources and job execution.

    Features:
        - Priority-based job queue
        - Automatic job scheduling based on resources
        - Graceful degradation under load
        - Job cancellation and cleanup
        - Resource allocation strategy

    Usage:
        ```python
        manager = ResourceManager(
            thread_pool=threadpool,
            resource_monitor=monitor
        )

        # Submit job
        job_id = manager.submit_job(
            worker=AnalysisWorker(...),
            priority=JobPriority.HIGH,
            on_complete=handle_result,
            on_error=handle_error
        )

        # Cancel job
        manager.cancel_job(job_id)

        # Shutdown
        manager.shutdown()
        ```
    """

    # Signals
    job_queued = Signal(str)  # job_id
    job_started = Signal(str)  # job_id
    job_completed = Signal(str)  # job_id
    job_failed = Signal(str, str)  # job_id, error
    job_cancelled = Signal(str)  # job_id
    job_denied = Signal(str, str)  # job_id, reason
    queue_size_changed = Signal(int)  # current queue size

    def __init__(
        self,
        thread_pool: QThreadPool | None = None,
        resource_monitor: ResourceMonitor | None = None,
        max_queue_size: int = 100,
        check_interval_ms: int = 500,
    ):
        """
        Initialize resource manager.

        Args:
            thread_pool: Qt thread pool (creates new if None)
            resource_monitor: Resource monitor (creates new if None)
            max_queue_size: Maximum queued jobs
            check_interval_ms: Job processing check interval
        """
        super().__init__()

        self.thread_pool = thread_pool or QThreadPool.globalInstance()
        self.resource_monitor = resource_monitor or ResourceMonitor()
        self.max_queue_size = max_queue_size

        # Job queue
        self._job_queue: PriorityQueue[Job] = PriorityQueue(maxsize=max_queue_size)
        self._active_jobs: dict[str, Job] = {}
        self._cancelled_jobs: set[str] = set()

        # Processing timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._process_queue)
        self._timer.start(check_interval_ms)

        # State
        self._is_shutting_down = False
        self._processing_queue = False

        logger.info(f"ResourceManager initialized (max_queue: {max_queue_size})")

    def submit_job(
        self,
        worker: BaseWorker,
        priority: JobPriority = JobPriority.NORMAL,
        on_complete: Callable[[Any], None] | None = None,
        on_error: Callable[[tuple], None] | None = None,
    ) -> str:
        """
        Submit a job for execution.

        Args:
            worker: Worker instance to execute
            priority: Job priority level
            on_complete: Callback for successful completion
            on_error: Callback for errors

        Returns:
            Job ID string

        Raises:
            RuntimeError: If queue is full or shutting down
        """
        if self._is_shutting_down:
            raise RuntimeError("ResourceManager is shutting down")

        # Create job
        job = Job(
            priority=priority.value,
            worker=worker,
            callback=on_complete,
            error_callback=on_error,
            job_type=worker.job_type,
        )

        # Check queue capacity (queued + active) before enqueuing to enforce hard limits.
        current_load = self.get_total_job_count()
        if current_load >= self.max_queue_size or self._job_queue.full():
            logger.warning(f"Job capacity reached ({current_load}/{self.max_queue_size}), denying job {job.job_id}")
            self.job_denied.emit(job.job_id, "Queue full")
            raise RuntimeError(f"Queue full (max: {self.max_queue_size})")

        # Add to queue
        try:
            self._job_queue.put_nowait(job)
            logger.info(f"Job queued: {job.job_id} (priority: {priority.name}, type: {job.job_type})")
            self.job_queued.emit(job.job_id)
            self.queue_size_changed.emit(self._job_queue.qsize())
            self._process_queue()

            return job.job_id

        except Exception as e:
            logger.error(f"Failed to queue job: {e}")
            self.job_denied.emit(job.job_id, str(e))
            raise

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job (queued or active).

        Args:
            job_id: Job ID to cancel

        Returns:
            True if job was cancelled
        """
        # Mark as cancelled
        self._cancelled_jobs.add(job_id)

        # Cancel active job
        if job_id in self._active_jobs:
            job = self._active_jobs[job_id]
            job.worker.cancel()
            logger.info(f"Cancelled active job: {job_id}")
            self.job_cancelled.emit(job_id)
            return True

        # Job is queued (will be skipped in _process_queue)
        logger.info(f"Marked queued job for cancellation: {job_id}")
        self.job_cancelled.emit(job_id)
        return True

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._job_queue.qsize()

    def get_active_job_count(self) -> int:
        """Get number of active jobs."""
        return len(self._active_jobs)

    def get_total_job_count(self) -> int:
        """Get total jobs (queued + active)."""
        return self.get_queue_size() + self.get_active_job_count()

    def _process_queue(self):
        """Process job queue (called periodically)."""
        if self._is_shutting_down:
            return

        if self._processing_queue:
            return

        self._processing_queue = True
        try:
            # Check if we can start more jobs
            available_threads = self.thread_pool.maxThreadCount() - self.thread_pool.activeThreadCount()

            if available_threads <= 0:
                return  # Thread pool full

            # Process jobs by priority
            jobs_to_start = []

            while not self._job_queue.empty() and len(jobs_to_start) < available_threads:
                try:
                    job = self._job_queue.get_nowait()

                    # Skip cancelled jobs
                    if job.job_id in self._cancelled_jobs:
                        self._cancelled_jobs.remove(job.job_id)
                        continue

                    jobs_to_start.append(job)

                except Exception:
                    break

            # Start jobs
            for job in jobs_to_start:
                self._start_job(job)

            # Update queue size
            if jobs_to_start:
                self.queue_size_changed.emit(self._job_queue.qsize())
        finally:
            self._processing_queue = False

    def _start_job(self, job: Job):
        """
        Start a job in the thread pool.

        Args:
            job: Job to start
        """
        # Check resources
        can_start, reason = self.resource_monitor.can_start_job(job.job_type)

        if not can_start:
            logger.warning(f"Job {job.job_id} denied due to resources: {reason}")
            self.job_denied.emit(job.job_id, reason)

            # Re-queue with lower priority if not critical
            if job.priority > JobPriority.CRITICAL.value:
                logger.info(f"Re-queueing job {job.job_id} with lower priority")
                job.priority += 1  # Lower priority
                try:
                    self._job_queue.put_nowait(job)
                except Exception:
                    logger.error(f"Failed to re-queue job {job.job_id}")

            return

        # Connect signals
        job.worker.signals.finished.connect(lambda: self._on_job_finished(job))
        job.worker.signals.result.connect(lambda result: self._on_job_result(job, result))
        job.worker.signals.error.connect(lambda error: self._on_job_error(job, error))

        # Add to active jobs
        self._active_jobs[job.job_id] = job

        # Start worker
        self.thread_pool.start(job.worker)

        logger.info(f"Job started: {job.job_id} (active: {len(self._active_jobs)})")
        self.job_started.emit(job.job_id)

    def _on_job_finished(self, job: Job):
        """Handle job completion."""
        if job.job_id in self._active_jobs:
            del self._active_jobs[job.job_id]

        logger.info(f"Job finished: {job.job_id}")

        if not self._is_shutting_down:
            self._process_queue()

    def _on_job_result(self, job: Job, result: Any):
        """Handle job result."""
        logger.info(f"Job completed successfully: {job.job_id}")
        self.job_completed.emit(job.job_id)

        # Call user callback
        if job.callback:
            try:
                job.callback(result)
            except Exception as e:
                logger.error(f"Job callback failed for {job.job_id}: {e}")

    def _on_job_error(self, job: Job, error: tuple):
        """Handle job error."""
        exc_type, exc_value, traceback_str = error
        logger.error(f"Job failed: {job.job_id} - {exc_value}")
        self.job_failed.emit(job.job_id, str(exc_value))

        # Call user error callback
        if job.error_callback:
            try:
                job.error_callback(error)
            except Exception as e:
                logger.error(f"Job error callback failed for {job.job_id}: {e}")

    def shutdown(self, wait: bool = True):
        """
        Shutdown resource manager.

        Args:
            wait: Wait for active jobs to complete
        """
        logger.info("ResourceManager shutting down...")
        self._is_shutting_down = True

        # Stop processing queue
        self._timer.stop()

        # Cancel all queued jobs
        while not self._job_queue.empty():
            try:
                job = self._job_queue.get_nowait()
                self.job_cancelled.emit(job.job_id)
            except Exception:
                break

        # Cancel active jobs
        for job_id in list(self._active_jobs.keys()):
            self.cancel_job(job_id)

        # Wait for thread pool
        if wait:
            self.thread_pool.waitForDone(5000)  # 5 second timeout

        logger.info("ResourceManager shutdown complete")

    def get_statistics(self) -> dict:
        """
        Get resource manager statistics.

        Returns:
            Dict with queue size, active jobs, etc.
        """
        return {
            "queue_size": self.get_queue_size(),
            "active_jobs": self.get_active_job_count(),
            "total_jobs": self.get_total_job_count(),
            "max_queue_size": self.max_queue_size,
            "thread_pool_max": self.thread_pool.maxThreadCount(),
            "thread_pool_active": self.thread_pool.activeThreadCount(),
            "is_shutting_down": self._is_shutting_down,
        }
