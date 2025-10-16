"""
Worker Thread Manager for Background Processing
Handles heavy computations without blocking the main thread
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from typing import Any
from collections.abc import Callable
from uuid import uuid4

import structlog

logger = structlog.get_logger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Exception | None = None
    progress: float = 0.0
    started_at: float | None = None
    completed_at: float | None = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ProgressCallback:
    """Thread-safe progress callback for long-running tasks"""

    def __init__(self, task_id: str, manager: 'WorkerManager'):
        self.task_id = task_id
        self.manager = manager
        self._lock = threading.Lock()

    def update(self, progress: float, message: str = "", metadata: dict[str, Any] = None):
        """Update task progress (thread-safe)"""
        with self._lock:
            self.manager._update_task_progress(self.task_id, progress, message, metadata or {})

    def set_status(self, status: TaskStatus, message: str = ""):
        """Update task status (thread-safe)"""
        with self._lock:
            self.manager._update_task_status(self.task_id, status, message)


class WorkerManager:
    """Manages background worker threads for heavy processing tasks"""

    def __init__(self, max_workers: int = 4, max_queue_size: int = 100):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="worker")
        self.tasks: dict[str, TaskResult] = {}
        self.futures: dict[str, Any] = {}
        self._lock = threading.RLock()
        self._shutdown = False

        # Start cleanup task
        self._cleanup_thread = threading.Thread(target=self._cleanup_completed_tasks, daemon=True)
        self._cleanup_thread.start()

        logger.info("WorkerManager initialized", max_workers=max_workers, max_queue_size=max_queue_size)

    def submit_task(
        self,
        func: Callable,
        *args,
        task_id: str | None = None,
        priority: int = 0,
        timeout: float | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs
    ) -> str:
        """Submit a task for background processing"""

        if self._shutdown:
            raise RuntimeError("WorkerManager is shutting down")

        if len(self.tasks) >= self.max_queue_size:
            raise RuntimeError(f"Task queue is full (max: {self.max_queue_size})")

        task_id = task_id or str(uuid4())

        with self._lock:
            if task_id in self.tasks:
                raise ValueError(f"Task {task_id} already exists")

            # Create task result
            task_result = TaskResult(
                task_id=task_id,
                status=TaskStatus.PENDING,
                metadata=metadata or {}
            )
            self.tasks[task_id] = task_result

            # Create progress callback
            progress_callback = ProgressCallback(task_id, self)

            # Submit to executor
            future = self.executor.submit(
                self._execute_task,
                task_id,
                func,
                progress_callback,
                timeout,
                *args,
                **kwargs
            )
            self.futures[task_id] = future

            logger.info("Task submitted", task_id=task_id, function=func.__name__)
            return task_id

    def _execute_task(
        self,
        task_id: str,
        func: Callable,
        progress_callback: ProgressCallback,
        timeout: float | None,
        *args,
        **kwargs
    ):
        """Execute a task with error handling and progress tracking"""

        start_time = time.time()

        try:
            with self._lock:
                task = self.tasks.get(task_id)
                if task:
                    task.status = TaskStatus.RUNNING
                    task.started_at = start_time

            logger.info("Task started", task_id=task_id)

            # Add progress callback to kwargs if function accepts it
            import inspect
            sig = inspect.signature(func)
            if 'progress_callback' in sig.parameters:
                kwargs['progress_callback'] = progress_callback

            # Execute with timeout if specified
            if timeout:
                result = self._execute_with_timeout(func, timeout, *args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Mark as completed
            with self._lock:
                task = self.tasks.get(task_id)
                if task:
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                    task.completed_at = time.time()
                    task.progress = 1.0

            logger.info("Task completed", task_id=task_id, duration=time.time() - start_time)

        except Exception as e:
            logger.exception("Task failed", task_id=task_id, error=str(e))

            with self._lock:
                task = self.tasks.get(task_id)
                if task:
                    task.status = TaskStatus.FAILED
                    task.error = e
                    task.completed_at = time.time()

    def _execute_with_timeout(self, func: Callable, timeout: float, *args, **kwargs):
        """Execute function with timeout"""
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError(f"Task timed out after {timeout} seconds")

        # Set timeout (Unix only)
        if hasattr(signal, 'SIGALRM'):
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout))

            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # Cancel alarm
                return result
            finally:
                signal.signal(signal.SIGALRM, old_handler)
        else:
            # Fallback for Windows - use threading
            result_container = []
            exception_container = []

            def target():
                try:
                    result_container.append(func(*args, **kwargs))
                except Exception as e:
                    exception_container.append(e)

            thread = threading.Thread(target=target)
            thread.start()
            thread.join(timeout)

            if thread.is_alive():
                # Thread is still running, timeout occurred
                raise TimeoutError(f"Task timed out after {timeout} seconds")

            if exception_container:
                raise exception_container[0]

            return result_container[0] if result_container else None

    def _update_task_progress(self, task_id: str, progress: float, message: str, metadata: dict[str, Any]):
        """Update task progress (internal method)"""
        with self._lock:
            task = self.tasks.get(task_id)
            if task and task.status == TaskStatus.RUNNING:
                task.progress = max(0.0, min(1.0, progress))
                task.metadata.update(metadata)
                if message:
                    task.metadata['status_message'] = message

    def _update_task_status(self, task_id: str, status: TaskStatus, message: str):
        """Update task status (internal method)"""
        with self._lock:
            task = self.tasks.get(task_id)
            if task:
                task.status = status
                if message:
                    task.metadata['status_message'] = message

    def get_task_status(self, task_id: str) -> TaskResult | None:
        """Get current status of a task"""
        with self._lock:
            return self.tasks.get(task_id)

    def get_task_result(self, task_id: str, timeout: float | None = None) -> TaskResult:
        """Wait for task completion and return result"""
        future = self.futures.get(task_id)
        if not future:
            raise ValueError(f"Task {task_id} not found")

        try:
            # Wait for completion
            future.result(timeout=timeout)
        except Exception:
            pass  # Error is already stored in task result

        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")

            return task

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        future = self.futures.get(task_id)
        if not future:
            return False

        cancelled = future.cancel()

        if cancelled:
            with self._lock:
                task = self.tasks.get(task_id)
                if task:
                    task.status = TaskStatus.CANCELLED
                    task.completed_at = time.time()

            logger.info("Task cancelled", task_id=task_id)

        return cancelled

    def list_tasks(self, status_filter: TaskStatus | None = None) -> list[TaskResult]:
        """List all tasks, optionally filtered by status"""
        with self._lock:
            tasks = list(self.tasks.values())

            if status_filter:
                tasks = [task for task in tasks if task.status == status_filter]

            return tasks

    def get_stats(self) -> dict[str, Any]:
        """Get worker manager statistics"""
        with self._lock:
            total_tasks = len(self.tasks)
            status_counts = {}

            for task in self.tasks.values():
                status_counts[task.status.value] = status_counts.get(task.status.value, 0) + 1

            return {
                'total_tasks': total_tasks,
                'status_counts': status_counts,
                'max_workers': self.max_workers,
                'active_workers': len([f for f in self.futures.values() if not f.done()]),
                'queue_size': len([task for task in self.tasks.values() if task.status == TaskStatus.PENDING])
            }

    def _cleanup_completed_tasks(self):
        """Background thread to clean up old completed tasks"""
        while not self._shutdown:
            try:
                current_time = time.time()
                cleanup_threshold = 3600  # 1 hour

                with self._lock:
                    tasks_to_remove = []

                    for task_id, task in self.tasks.items():
                        if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                            task.completed_at and
                            current_time - task.completed_at > cleanup_threshold):
                            tasks_to_remove.append(task_id)

                    for task_id in tasks_to_remove:
                        self.tasks.pop(task_id, None)
                        self.futures.pop(task_id, None)

                    if tasks_to_remove:
                        logger.info("Cleaned up completed tasks", count=len(tasks_to_remove))

                time.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.exception("Error in cleanup thread", error=str(e))
                time.sleep(60)  # Wait before retrying

    def shutdown(self, wait: bool = True, timeout: float | None = None):
        """Shutdown the worker manager"""
        logger.info("Shutting down WorkerManager")

        self._shutdown = True

        # Cancel all pending tasks
        with self._lock:
            for task_id in list(self.futures.keys()):
                self.cancel_task(task_id)

        # Shutdown executor
        self.executor.shutdown(wait=wait, timeout=timeout)

        logger.info("WorkerManager shutdown complete")


# Global worker manager instance
_worker_manager: WorkerManager | None = None


def get_worker_manager() -> WorkerManager:
    """Get the global worker manager instance"""
    global _worker_manager
    if _worker_manager is None:
        _worker_manager = WorkerManager()
    return _worker_manager


def shutdown_worker_manager():
    """Shutdown the global worker manager"""
    global _worker_manager
    if _worker_manager:
        _worker_manager.shutdown()
        _worker_manager = None


# Example usage functions for common tasks
def submit_document_analysis(
    document_content: str,
    rubric_id: str,
    analysis_options: dict[str, Any],
    task_id: str | None = None
) -> str:
    """Submit document analysis task"""

    def analyze_document(content: str, rubric: str, options: dict[str, Any], progress_callback: ProgressCallback):
        # This would be implemented to use the actual analysis service
        progress_callback.update(0.1, "Starting analysis...")

        # Simulate analysis steps
        import time
        for i in range(10):
            time.sleep(0.5)  # Simulate work
            progress_callback.update((i + 1) / 10, f"Processing step {i + 1}/10")

        return {"analysis": "completed", "findings": []}

    worker_manager = get_worker_manager()
    return worker_manager.submit_task(
        analyze_document,
        document_content,
        rubric_id,
        analysis_options,
        task_id=task_id,
        metadata={"type": "document_analysis", "rubric_id": rubric_id}
    )


def submit_pdf_processing(
    pdf_path: str,
    processing_options: dict[str, Any],
    task_id: str | None = None
) -> str:
    """Submit PDF processing task"""

    def process_pdf(path: str, options: dict[str, Any], progress_callback: ProgressCallback):
        # This would be implemented to use actual PDF processing
        progress_callback.update(0.1, "Loading PDF...")

        # Simulate PDF processing
        import time
        for i in range(5):
            time.sleep(1)  # Simulate work
            progress_callback.update((i + 1) / 5, f"Processing page {i + 1}/5")

        return {"pages": 5, "text": "extracted text"}

    worker_manager = get_worker_manager()
    return worker_manager.submit_task(
        process_pdf,
        pdf_path,
        processing_options,
        task_id=task_id,
        metadata={"type": "pdf_processing", "file_path": pdf_path}
    )
