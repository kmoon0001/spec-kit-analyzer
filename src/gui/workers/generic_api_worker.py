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
    finished = Signal()  # Added finished signal

    def __init__(self, token: str, feedback_data: dict[str, Any], parent: QThread | None = None) -> None:
        super().__init__()
        self.token = token
        self.feedback_data = feedback_data
        self._should_stop = False

    def run(self) -> None:
        if self._should_stop:
            return
        try:
            url = f"{API_URL}/feedback/"
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(url, headers=headers, json=self.feedback_data, timeout=10)
            response.raise_for_status()
            if not self._should_stop:
                self.success.emit("Feedback submitted successfully!")
        except requests.HTTPError as e:
            if not self._should_stop:
                self.error.emit(f"Failed to submit feedback: {e.response.status_code}")
        except requests.RequestException as e:
            if not self._should_stop:
                self.error.emit(f"Network error during feedback submission: {e}")
        finally:
            self.finished.emit()  # Emit finished signal

    def stop(self) -> None:
        """Stop the worker gracefully."""
        self._should_stop = True


class GenericApiWorker(QThread):
    """A worker that fetches data from a specified API endpoint."""

    success = Signal(object)
    error = Signal(str)
    finished = Signal()  # Added finished signal

    def __init__(self, method: str, endpoint: str, data: dict = None, token: str = None, parent=None):
        super().__init__()
        self.method = method.upper()
        self.endpoint = endpoint
        self.data = data or {}
        self.token = token
        self.is_running = False
        self._should_stop = False

    def run(self):
        if self._should_stop:
            return
        self.is_running = True
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            url = f"{API_URL}{self.endpoint}"

            if self.method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif self.method == "POST":
                response = requests.post(url, json=self.data, headers=headers, timeout=30)
            elif self.method == "PUT":
                response = requests.put(url, json=self.data, headers=headers, timeout=30)
            elif self.method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                if not self._should_stop:
                    self.error.emit(f"Unsupported method: {self.method}")
                return

            if not self._should_stop:
                if response.status_code in [200, 201]:
                    self.success.emit(response.json())
                else:
                    self.error.emit(f"API error: {response.status_code} - {response.text}")

        except Exception as e:
            if not self._should_stop:
                self.error.emit(f"Request failed: {str(e)}")
        finally:
            self.is_running = False
            self.finished.emit()  # Emit finished signal

    def stop(self) -> None:
        """Stop the worker gracefully."""
        self._should_stop = True


class TaskMonitorWorker(QThread):
    """A worker that periodically fetches the list of all tasks."""

    tasks_updated = Signal(dict)
    error = Signal(str)
    finished = Signal()  # Added finished signal

    def __init__(self, token: str = None, parent=None):
        super().__init__()
        self.token = token
        self.running = False
        self._should_stop = False

    def run(self):
        if self._should_stop:
            return
        self.running = True
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        while self.running and not self._should_stop:
            try:
                response = requests.get(f"{API_URL}/tasks", headers=headers, timeout=5)
                if response.status_code == 200:
                    tasks_data = response.json()
                    if not self._should_stop:
                        self.tasks_updated.emit(tasks_data)
                else:
                    if not self._should_stop:
                        self.error.emit(f"Task list fetch error: {response.status_code}")
                    break

                # Replace long sleep with shorter, responsive sleeps
                for _ in range(50):  # Check every 100ms for 5 seconds
                    if not self.running or self._should_stop:
                        break
                    self.msleep(100)

            except Exception as e:
                if not self._should_stop:
                    self.error.emit(f"Task monitoring failed: {str(e)}")
                break
        self.finished.emit()  # Emit finished signal

    def stop(self):
        """Stop the worker gracefully."""
        self.running = False
        self._should_stop = True


__all__ = ["GenericApiWorker", "TaskMonitorWorker", "FeedbackWorker"]


class HealthCheckWorker(QThread):
    """Worker to check API health status."""

    success = Signal(dict)
    error = Signal(str)
    finished = Signal()  # Added finished signal

    def __init__(self, parent=None):
        super().__init__()
        self.running = False
        self._should_stop = False

    def run(self):
        if self._should_stop:
            return
        self.running = True
        while self.running and not self._should_stop:
            try:
                response = requests.get(f"{API_URL}/health", timeout=5)
                if response.status_code == 200:
                    if not self._should_stop:
                        self.success.emit(response.json())
                else:
                    if not self._should_stop:
                        self.error.emit(f"Health check failed: {response.status_code}")
            except Exception as e:
                if not self._should_stop:
                    self.error.emit(f"Health check error: {str(e)}")

            # Replace long sleep with shorter, responsive sleeps
            for _ in range(100):  # Check every 100ms for 10 seconds
                if not self.running or self._should_stop:
                    break
                self.msleep(100)
        self.finished.emit()  # Emit finished signal

    def stop(self):
        """Stop the worker gracefully."""
        self.running = False
        self._should_stop = True


class LogStreamWorker(QThread):
    """Worker to stream logs from the API."""

    log_received = Signal(str)
    error = Signal(str)
    finished = Signal()  # Added finished signal

    def __init__(self, token: str = None, parent=None):
        super().__init__()
        self.token = token
        self.running = False
        self._should_stop = False

    def run(self):
        if self._should_stop:
            return
        self.running = True
        try:
            # Simple log streaming implementation
            while self.running and not self._should_stop:
                try:
                    headers = {}
                    if self.token:
                        headers["Authorization"] = f"Bearer {self.token}"

                    response = requests.get(f"{API_URL}/logs/stream", headers=headers, timeout=1)
                    if response.status_code == 200:
                        if not self._should_stop:
                            self.log_received.emit(response.text)
                except requests.exceptions.Timeout:
                    pass  # Normal timeout, keep trying
                except Exception as e:
                    if not self._should_stop:
                        self.error.emit(f"Log stream error: {str(e)}")
                    break
                self.msleep(50)  # Add a small sleep to yield control and check self.running
        except Exception as e:
            if not self._should_stop:
                self.error.emit(f"Log stream failed: {str(e)}")
        finally:
            self.finished.emit()  # Emit finished signal

    def stop(self):
        """Stop the worker gracefully."""
        self.running = False
        self._should_stop = True
