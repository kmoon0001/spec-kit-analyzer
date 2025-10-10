"""Centralized manager for handling the auto-analysis queue.

This module provides a singleton QueueManager that maintains the state of the
batch analysis queue, including the list of files to be processed, their
statuses, and the overall progress. This decouples the queue management from
the UI and allows it to be accessed from different parts of the application.
"""

from typing import Any, ClassVar, Optional

from PySide6.QtCore import QObject, Signal


class QueueManager(QObject):
    """A singleton class to manage the auto-analysis queue."""

    _instance: ClassVar[Optional["QueueManager"]] = None

    queue: list[dict[str, Any]]
    is_running: bool

    queue_updated = Signal()
    progress_updated = Signal(int, int)

    def __new__(cls):
        if cls._instance is None:
            instance = super().__new__(cls)
            instance.queue = []
            instance.is_running = False
            cls._instance = instance
        return cls._instance

    def add_files(self, files: list[str]):
        """Adds a list of files to the queue."""
        for file in files:
            self.queue.append({"path": file, "status": "Pending"})
        self.queue_updated.emit()

    def get_queue(self) -> list[dict[str, Any]]:
        """Returns the current state of the queue."""
        return self.queue

    def update_file_status(self, file_path: str, status: str):
        """Updates the status of a file in the queue."""
        for item in self.queue:
            if item["path"] == file_path:
                item["status"] = status
                break
        self.queue_updated.emit()

    def start_processing(self):
        """Marks the queue as running."""
        self.is_running = True

    def stop_processing(self):
        """Marks the queue as not running."""
        self.is_running = False

    def clear_queue(self):
        """Clears the queue."""
        self.queue.clear()
        self.queue_updated.emit()

    def set_progress(self, current: int, total: int):
        """Emits the progress of the batch analysis."""
        self.progress_updated.emit(current, total)

# Global instance of the QueueManager
queue_manager = QueueManager()

def get_queue_manager() -> QueueManager:
    """Returns the global instance of the QueueManager."""
    return queue_manager
