"""
Enhanced Worker Manager with ProcessPoolExecutor and Retry Logic
Replaces ThreadPoolExecutor with ProcessPoolExecutor for better AI task handling
"""

import asyncio
import logging
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

import structlog

logger = structlog.get_logger(__name__)


class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class WorkerTask:
    task_id: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: TaskPriority
    timeout: Optional[float]
    created_at: float
    retry_count: int = 0
    max_retries: int = 3
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error_message: Optional[str] = None
    result: Any = None


class EnhancedWorkerManager:
    """Enhanced worker manager with process pools and retry logic."""

    def __init__(self, max_workers: int = 2, max_queue_size: int = 50):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.executor = ProcessPoolExecutor(max_workers=max_workers)
        self.tasks: Dict[str, WorkerTask] = {}
        self.futures: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._shutdown = False
        self._task_queue = asyncio.PriorityQueue()
        self._worker_task = None

        logger.info(
            "Enhanced WorkerManager initialized",
            max_workers=max_workers,
            max_queue_size=max_queue_size,
        )

    async def start(self) -> None:
        """Start the worker manager."""
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker_loop())
            logger.info("Worker manager started")

    async def stop(self) -> None:
        """Stop the worker manager gracefully."""
        self._shutdown = True

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        # Cancel all pending futures
        for future in self.futures.values():
            future.cancel()

        # Shutdown executor
        self.executor.shutdown(wait=True)
        logger.info("Worker manager stopped")

    async def submit_task(
        self,
        func: Callable,
        *args,
        task_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
        max_retries: int = 3,
        **kwargs,
    ) -> str:
        """Submit a task for background processing with retry logic."""

        if self._shutdown:
            raise RuntimeError("WorkerManager is shutting down")

        async with self._lock:
            if len(self.tasks) >= self.max_queue_size:
                raise RuntimeError(f"Task queue is full (max: {self.max_queue_size})")

            task_id = task_id or str(uuid4())

            if task_id in self.tasks:
                raise ValueError(f"Task {task_id} already exists")

            task = WorkerTask(
                task_id=task_id,
                func=func,
                args=args,
                kwargs=kwargs,
                priority=priority,
                timeout=timeout,
                max_retries=max_retries,
                created_at=time.time(),
            )

            self.tasks[task_id] = task

            # Add to priority queue
            await self._task_queue.put((priority.value, task_id))

            logger.info(
                "Task submitted",
                task_id=task_id,
                priority=priority.value,
                max_retries=max_retries,
            )

            return task_id

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a task."""
        task = self.tasks.get(task_id)
        if not task:
            return None

        status = "pending"
        if task.started_at and not task.completed_at:
            status = "running"
        elif task.completed_at:
            status = "completed" if task.result is not None else "failed"
        elif task.error_message:
            status = "failed"

        return {
            "task_id": task_id,
            "status": status,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "error_message": task.error_message,
            "priority": task.priority.value,
        }

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task."""
        async with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return False

            # Cancel future if it exists
            future = self.futures.get(task_id)
            if future and not future.done():
                future.cancel()
                logger.info("Task cancelled", task_id=task_id)
                return True

            return False

    async def get_task_result(self, task_id: str) -> Any:
        """Get the result of a completed task."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if not task.completed_at:
            raise ValueError(f"Task {task_id} not completed")

        if task.error_message:
            raise RuntimeError(f"Task {task_id} failed: {task.error_message}")

        return task.result

    async def cleanup_completed_tasks(self, max_age_hours: int = 24) -> int:
        """Clean up completed tasks older than specified hours."""
        async with self._lock:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600

            tasks_to_remove = []
            for task_id, task in self.tasks.items():
                if (
                    task.completed_at
                    and current_time - task.completed_at > max_age_seconds
                ):
                    tasks_to_remove.append(task_id)

            for task_id in tasks_to_remove:
                del self.tasks[task_id]
                self.futures.pop(task_id, None)

            if tasks_to_remove:
                logger.info("Cleaned up completed tasks", count=len(tasks_to_remove))

            return len(tasks_to_remove)

    async def get_statistics(self) -> Dict[str, Any]:
        """Get worker manager statistics."""
        async with self._lock:
            total_tasks = len(self.tasks)
            pending_tasks = sum(
                1 for task in self.tasks.values() if not task.started_at
            )
            running_tasks = sum(
                1
                for task in self.tasks.values()
                if task.started_at and not task.completed_at
            )
            completed_tasks = sum(
                1
                for task in self.tasks.values()
                if task.completed_at and task.result is not None
            )
            failed_tasks = sum(1 for task in self.tasks.values() if task.error_message)

            return {
                "total_tasks": total_tasks,
                "pending_tasks": pending_tasks,
                "running_tasks": running_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "max_workers": self.max_workers,
                "max_queue_size": self.max_queue_size,
                "queue_size": self._task_queue.qsize(),
            }

    async def _worker_loop(self) -> None:
        """Main worker loop that processes tasks from the priority queue."""
        logger.info("Worker loop started")

        while not self._shutdown:
            try:
                # Get next task from priority queue
                _, task_id = await asyncio.wait_for(self._task_queue.get(), timeout=1.0)

                task = self.tasks.get(task_id)
                if not task:
                    continue

                # Execute task
                await self._execute_task(task)

            except asyncio.TimeoutError:
                # No tasks in queue, continue
                continue
            except Exception as e:
                logger.error("Error in worker loop", error=str(e))
                await asyncio.sleep(1)

        logger.info("Worker loop stopped")

    async def _execute_task(self, task: WorkerTask) -> None:
        """Execute a single task with retry logic."""
        try:
            task.started_at = time.time()

            # Submit to process pool
            future = self.executor.submit(task.func, *task.args, **task.kwargs)
            self.futures[task.task_id] = future

            # Wait for completion with timeout
            if task.timeout:
                try:
                    result = await asyncio.wait_for(
                        asyncio.wrap_future(future), timeout=task.timeout
                    )
                    task.result = result
                    task.completed_at = time.time()

                    logger.info(
                        "Task completed",
                        task_id=task.task_id,
                        duration=task.completed_at - task.started_at,
                    )

                except asyncio.TimeoutError:
                    future.cancel()
                    task.error_message = f"Task timed out after {task.timeout} seconds"
                    task.completed_at = time.time()

                    logger.warning(
                        "Task timed out", task_id=task.task_id, timeout=task.timeout
                    )
            else:
                result = await asyncio.wrap_future(future)
                task.result = result
                task.completed_at = time.time()

                logger.info(
                    "Task completed",
                    task_id=task.task_id,
                    duration=task.completed_at - task.started_at,
                )

        except Exception as e:
            task.error_message = str(e)
            task.completed_at = time.time()

            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.started_at = None
                task.error_message = None

                # Exponential backoff
                delay = min(2**task.retry_count, 60)  # Max 60 seconds
                await asyncio.sleep(delay)

                # Re-queue task
                await self._task_queue.put((task.priority.value, task.task_id))

                logger.info(
                    "Task retry scheduled",
                    task_id=task.task_id,
                    retry_count=task.retry_count,
                    delay=delay,
                )
            else:
                logger.error(
                    "Task failed after max retries",
                    task_id=task.task_id,
                    error=str(e),
                    retry_count=task.retry_count,
                )

        finally:
            # Clean up future reference
            self.futures.pop(task.task_id, None)


# Global enhanced worker manager instance
enhanced_worker_manager = EnhancedWorkerManager()
