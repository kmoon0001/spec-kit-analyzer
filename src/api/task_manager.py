import asyncio
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class Task:
    """Represents a long-running analysis task with progress and subscribers."""
    def __init__(self, task_id: str, filename: str):
        self.task_id = task_id
        self.filename = filename
        self.status: str = "processing"
        self.progress: int = 0
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self._subscribers: List[asyncio.Queue] = []

    async def update_progress(self, progress: int, message: str = ""):
        """Update the task's progress and notify subscribers."""
        self.progress = progress
        await self._notify({"status": self.status, "progress": self.progress, "message": message})

    async def set_completed(self, result: Dict[str, Any]):
        """Mark the task as completed and notify subscribers."""
        self.status = "completed"
        self.progress = 100
        self.result = result
        await self._notify({"status": "completed", "result": self.result})
        await self._close_subscribers()

    async def set_failed(self, error: str):
        """Mark the task as failed and notify subscribers."""
        self.status = "failed"
        self.error = error
        await self._notify({"status": "failed", "error": self.error})
        await self._close_subscribers()

    def subscribe(self) -> asyncio.Queue:
        """Subscribe to task updates."""
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from task updates."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    async def _notify(self, message: Dict[str, Any]):
        """Notify all subscribers of an update."""
        for queue in self._subscribers:
            await queue.put(message)

    async def _close_subscribers(self):
        """Signal to all subscribers that the task is finished by putting None in the queue."""
        for queue in self._subscribers:
            await queue.put(None)

class TaskManager:
    """Manages all active analysis tasks."""
    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._lock = asyncio.Lock()

    async def create_task(self, task_id: str, filename: str) -> Task:
        """Create and register a new task."""
        async with self._lock:
            if task_id in self._tasks:
                raise ValueError(f"Task with ID {task_id} already exists.")
            task = Task(task_id=task_id, filename=filename)
            self._tasks[task_id] = task
            logger.info("Created and registered new task: %s", task_id)
            return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieve a task by its ID."""
        async with self._lock:
            return self._tasks.get(task_id)

    async def remove_task(self, task_id: str):
        """Remove a task, e.g., after it's completed and fetched."""
        async with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                logger.info("Removed task from manager: %s", task_id)

# Singleton instance to be used across the application
task_manager = TaskManager()
