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

class HealthCheckWorker(QThread):
    """Worker to check API health status."""
    
    success = Signal(dict)
    error = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def run(self):
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            if response.status_code == 200:
                self.success.emit(response.json())
            else:
                self.error.emit(f"Health check failed: {response.status_code}")
        except Exception as e:
            self.error.emit(f"Health check error: {str(e)}")
class 
LogStreamWorker(QThread):
    """Worker to stream logs from the API."""
    
    log_received = Signal(str)
    error = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
    
    def run(self):
        self.running = True
        try:
            # Simple log streaming implementation
            while self.running:
                try:
                    response = requests.get(f"{API_URL}/logs/stream", timeout=1)
                    if response.status_code == 200:
                        self.log_received.emit(response.text)
                except requests.exceptions.Timeout:
                    continue  # Normal timeout, keep trying
                except Exception as e:
                    self.error.emit(f"Log stream error: {str(e)}")
                    break
        except Exception as e:
            self.error.emit(f"Log stream failed: {str(e)}")
    
    def stop(self):
        self.running = False