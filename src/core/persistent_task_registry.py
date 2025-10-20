"""
Persistent Task Registry with SQLite Storage
Replaces in-memory task tracking with persistent storage
"""

import asyncio
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class TaskMetadata:
    task_id: str
    status: TaskStatus
    progress: int = 0
    status_message: str = ""
    filename: str = ""
    user_id: int = 0
    discipline: str = ""
    analysis_mode: str = ""
    strictness: str = ""
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    result_data: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class PersistentTaskRegistry:
    """Persistent task registry using SQLite for task state management."""

    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self._lock = asyncio.Lock()
        self._init_database()

    def _init_database(self) -> None:
        """Initialize the SQLite database with task table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        task_id TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        progress INTEGER DEFAULT 0,
                        status_message TEXT DEFAULT '',
                        filename TEXT DEFAULT '',
                        user_id INTEGER DEFAULT 0,
                        discipline TEXT DEFAULT '',
                        analysis_mode TEXT DEFAULT '',
                        strictness TEXT DEFAULT '',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        started_at TIMESTAMP NULL,
                        completed_at TIMESTAMP NULL,
                        error_message TEXT NULL,
                        retry_count INTEGER DEFAULT 0,
                        max_retries INTEGER DEFAULT 3,
                        result_data TEXT NULL
                    )
                """)

                # Create indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)")

                conn.commit()
                logger.info("Task database initialized", db_path=self.db_path)

        except Exception as e:
            logger.error("Failed to initialize task database", error=str(e))
            raise

    async def create_task(self, task_id: str, **kwargs) -> TaskMetadata:
        """Create a new task in the registry."""
        async with self._lock:
            try:
                task = TaskMetadata(task_id=task_id, **kwargs)

                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT INTO tasks (
                            task_id, status, progress, status_message, filename,
                            user_id, discipline, analysis_mode, strictness,
                            created_at, retry_count, max_retries
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        task.task_id, task.status.value, task.progress, task.status_message,
                        task.filename, task.user_id, task.discipline, task.analysis_mode,
                        task.strictness, task.created_at.isoformat(), task.retry_count,
                        task.max_retries
                    ))
                    conn.commit()

                logger.info("Task created", task_id=task_id, status=task.status.value)
                return task

            except Exception as e:
                logger.error("Failed to create task", task_id=task_id, error=str(e))
                raise

    async def update_task(self, task_id: str, **kwargs) -> bool:
        """Update an existing task."""
        async with self._lock:
            try:
                # Build dynamic update query
                update_fields = []
                values = []

                for field, value in kwargs.items():
                    if field == 'status' and isinstance(value, TaskStatus):
                        value = value.value
                    elif field in ['created_at', 'started_at', 'completed_at'] and isinstance(value, datetime):
                        value = value.isoformat()
                    elif field == 'result_data' and isinstance(value, dict):
                        value = json.dumps(value)

                    update_fields.append(f"{field} = ?")
                    values.append(value)

                if not update_fields:
                    return True

                values.append(task_id)

                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        f"UPDATE tasks SET {', '.join(update_fields)} WHERE task_id = ?",
                        values
                    )
                    conn.commit()

                    if cursor.rowcount > 0:
                        logger.debug("Task updated", task_id=task_id, fields=list(kwargs.keys()))
                        return True
                    else:
                        logger.warning("Task not found for update", task_id=task_id)
                        return False

            except Exception as e:
                logger.error("Failed to update task", task_id=task_id, error=str(e))
                return False

    async def get_task(self, task_id: str) -> Optional[TaskMetadata]:
        """Get a task by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
                row = cursor.fetchone()

                if row:
                    return self._row_to_task(row)
                return None

        except Exception as e:
            logger.error("Failed to get task", task_id=task_id, error=str(e))
            return None

    async def get_tasks_by_user(self, user_id: int, limit: int = 50) -> List[TaskMetadata]:
        """Get tasks for a specific user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                    (user_id, limit)
                )
                rows = cursor.fetchall()

                return [self._row_to_task(row) for row in rows]

        except Exception as e:
            logger.error("Failed to get tasks by user", user_id=user_id, error=str(e))
            return []

    async def get_tasks_by_status(self, status: TaskStatus, limit: int = 100) -> List[TaskMetadata]:
        """Get tasks by status."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status.value, limit)
                )
                rows = cursor.fetchall()

                return [self._row_to_task(row) for row in rows]

        except Exception as e:
            logger.error("Failed to get tasks by status", status=status.value, error=str(e))
            return []

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        async with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
                    conn.commit()

                    if cursor.rowcount > 0:
                        logger.info("Task deleted", task_id=task_id)
                        return True
                    return False

            except Exception as e:
                logger.error("Failed to delete task", task_id=task_id, error=str(e))
                return False

    async def cleanup_old_tasks(self, days_old: int = 7) -> int:
        """Clean up tasks older than specified days."""
        async with self._lock:
            try:
                cutoff_date = datetime.now(timezone.utc).timestamp() - (days_old * 24 * 60 * 60)

                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        "DELETE FROM tasks WHERE created_at < ? AND status IN ('completed', 'failed', 'cancelled')",
                        (cutoff_date,)
                    )
                    conn.commit()

                    deleted_count = cursor.rowcount
                    if deleted_count > 0:
                        logger.info("Cleaned up old tasks", count=deleted_count, days_old=days_old)

                    return deleted_count

            except Exception as e:
                logger.error("Failed to cleanup old tasks", error=str(e))
                return 0

    async def get_task_statistics(self) -> Dict[str, Any]:
        """Get task statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Get counts by status
                cursor = conn.execute("""
                    SELECT status, COUNT(*) as count
                    FROM tasks
                    GROUP BY status
                """)
                status_counts = {row['status']: row['count'] for row in cursor.fetchall()}

                # Get total count
                cursor = conn.execute("SELECT COUNT(*) as total FROM tasks")
                total_tasks = cursor.fetchone()['total']

                # Get recent activity (last 24 hours)
                cursor = conn.execute("""
                    SELECT COUNT(*) as recent
                    FROM tasks
                    WHERE created_at > datetime('now', '-1 day')
                """)
                recent_tasks = cursor.fetchone()['recent']

                return {
                    'total_tasks': total_tasks,
                    'recent_tasks_24h': recent_tasks,
                    'status_counts': status_counts,
                    'database_path': self.db_path
                }

        except Exception as e:
            logger.error("Failed to get task statistics", error=str(e))
            return {}

    def _row_to_task(self, row: sqlite3.Row) -> TaskMetadata:
        """Convert database row to TaskMetadata object."""
        try:
            # Parse datetime fields
            created_at = datetime.fromisoformat(row['created_at'].replace('Z', '+00:00'))
            started_at = None
            if row['started_at']:
                started_at = datetime.fromisoformat(row['started_at'].replace('Z', '+00:00'))
            completed_at = None
            if row['completed_at']:
                completed_at = datetime.fromisoformat(row['completed_at'].replace('Z', '+00:00'))

            # Parse result data
            result_data = None
            if row['result_data']:
                try:
                    result_data = json.loads(row['result_data'])
                except json.JSONDecodeError:
                    logger.warning("Failed to parse result_data", task_id=row['task_id'])

            return TaskMetadata(
                task_id=row['task_id'],
                status=TaskStatus(row['status']),
                progress=row['progress'],
                status_message=row['status_message'],
                filename=row['filename'],
                user_id=row['user_id'],
                discipline=row['discipline'],
                analysis_mode=row['analysis_mode'],
                strictness=row['strictness'],
                created_at=created_at,
                started_at=started_at,
                completed_at=completed_at,
                error_message=row['error_message'],
                retry_count=row['retry_count'],
                max_retries=row['max_retries'],
                result_data=result_data
            )

        except Exception as e:
            logger.error("Failed to convert row to task", error=str(e))
            raise

    async def close(self) -> None:
        """Close the database connection."""
        # SQLite connections are automatically closed, but we can add cleanup here
        logger.info("Task registry closed")


# Global persistent task registry instance
persistent_task_registry = PersistentTaskRegistry()
