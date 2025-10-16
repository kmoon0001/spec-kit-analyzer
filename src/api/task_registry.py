from __future__ import annotations

import asyncio
import logging
from typing import Any
from collections.abc import Coroutine

logger = logging.getLogger(__name__)


class AnalysisTaskRegistry:
    """Tracks analysis task metadata and async handles for orchestration support."""

    def __init__(self) -> None:
        self.metadata: dict[str, dict[str, Any]] = {}
        self._handles: dict[str, asyncio.Task[Any]] = {}
        self._lock = asyncio.Lock()

    async def start(self, task_id: str, coroutine: Coroutine[Any, Any, Any]) -> asyncio.Task[Any]:
        """Schedule a coroutine for execution and register it under the given task id."""
        async with self._lock:
            task: asyncio.Task[Any] = asyncio.create_task(coroutine, name=f"analysis-{task_id}")
            self._handles[task_id] = task

            def _cleanup(_: asyncio.Future[Any]) -> None:
                self._handles.pop(task_id, None)

            task.add_done_callback(_cleanup)
            logger.debug("Registered analysis task %s", task_id)
            return task

    async def cancel(self, task_id: str) -> bool:
        """Request cancellation for the active coroutine associated with task_id."""
        async with self._lock:
            task = self._handles.get(task_id)
            if task is None:
                logger.debug("No active task handle found for %s", task_id)
                return False
            if task.done():
                self._handles.pop(task_id, None)
                logger.debug("Task %s already completed before cancellation", task_id)
                return False

            state = self.metadata.setdefault(task_id, {})
            if state.get("status") not in {"cancelled", "completed", "failed"}:
                state["status"] = "cancelling"
                state["status_message"] = "Cancellation requested by user."
            state["cancel_requested"] = True

            task.cancel()
            logger.info("Cancellation requested for analysis task %s", task_id)
            return True

    def get(self, task_id: str) -> dict[str, Any] | None:
        return self.metadata.get(task_id)

    def active_count(self) -> int:
        """Return the number of tasks that are not terminally completed."""
        return sum(
            1 for state in self.metadata.values() if state.get("status") not in {"completed", "failed", "cancelled"}
        )


analysis_task_registry = AnalysisTaskRegistry()
