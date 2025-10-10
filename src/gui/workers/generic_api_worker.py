"""Generic QThread workers for making API calls and handling background tasks."""

from __future__ import annotations

from typing import Any

import requests
from PySide6.QtCore import QThread, Signal

from src.config import get_settings

SETTINGS = get_settings()
API_URL = SETTINGS.paths.api_url
WS_URL = API_URL.replace("http", "ws")


class FeedbackWorker(QThread):
    """Worker to submit feedback to the API."""

    success = Signal(str)
    error = Signal(str)

    def __init__(self, token: str, feedback_data: dict[str, Any], parent: QThread | None = None) -> None:
        super().__init__(parent)
        self.token = token
        self.feedback_data = feedback_data

    def run(self) -> None:
        try:
            url = f"{API_URL}/feedback/"
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(url, headers=headers, json=self.feedback_data, timeout=10)
            response.raise_for_status()
            self.success.emit("Feedback submitted successfully!")
        except requests.HTTPError as e:
            self.error.emit(f"Failed to submit feedback: {e.response.status_code}")
        except requests.RequestException as e:
            self.error.emit(f"Network error during feedback submission: {e}")


class GenericApiWorker(QThread):
    """A worker that fetches data from a specified API endpoint."""

    success = Signal(object)
    error = Signal(str)

    def stop(self) -> None:
        self.is_running = False


class TaskMonitorWorker(QThread):
    """A worker that periodically fetches the list of all tasks."""

    tasks_updated = Signal(dict)
    error = Signal(str)


__all__ = ["GenericApiWorker", "TaskMonitorWorker", "FeedbackWorker"]
