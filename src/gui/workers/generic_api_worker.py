"""
Generic QThread workers for making API calls and handling background tasks.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Dict

import requests
import websockets
from PySide6.QtCore import QThread, Signal

from src.config import get_settings

SETTINGS = get_settings()
API_URL = SETTINGS.paths.api_url
WS_URL = API_URL.replace("http", "ws")


class FeedbackWorker(QThread):
    """Worker to submit feedback to the API."""
    success = Signal(str)
    error = Signal(str)

    def __init__(self, token: str, feedback_data: Dict[str, Any], parent: QThread | None = None) -> None:
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
    """
    A worker that fetches data from a specified API endpoint.
    """

    success = Signal(object)
    error = Signal(str)

    def __init__(self, endpoint: str, token: str, parent: QThread | None = None) -> None:
        super().__init__(parent)
        self.endpoint = endpoint
        self.token = token

    def run(self) -> None:
        """Fetches data from the API and emits success or error signal."""
        try:
            url = f"{API_URL}{self.endpoint}"
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.success.emit(data)
        except requests.HTTPError as e:
            self.error.emit(
                f"API error: {e.response.status_code} for {self.endpoint}"
            )
        except requests.RequestException as e:
            self.error.emit(f"Network error for {self.endpoint}: {e}")


class HealthCheckWorker(QThread):
    """
    A worker that periodically checks the API's /health endpoint.
    """

    status_update = Signal(str, str)  # status, color

    def __init__(self, parent: QThread | None = None) -> None:
        super().__init__(parent)
        self.is_running = True

    def run(self) -> None:
        """Periodically checks health and emits status_update signal."""
        while self.is_running:
            try:
                url = f"{API_URL}/health"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self.status_update.emit("Online", "#16a34a")  # Green
                else:
                    self.status_update.emit("Error", "#dc2626")  # Red
            except requests.RequestException:
                self.status_update.emit("Offline", "#dc2626")  # Red
            
            time.sleep(15)  # Wait 15 seconds before next check

    def stop(self) -> None:
        self.is_running = False


class TaskMonitorWorker(QThread):
    """
    A worker that periodically fetches the list of all tasks.
    """

    tasks_updated = Signal(dict)
    error = Signal(str)

    def __init__(self, token: str, parent: QThread | None = None) -> None:
        super().__init__(parent)
        self.token = token
        self.is_running = True

    def run(self) -> None:
        """Periodically fetches task data and emits tasks_updated signal."""
        while self.is_running:
            try:
                url = f"{API_URL}/analysis/all-tasks"
                headers = {"Authorization": f"Bearer {self.token}"}
                response = requests.get(url, headers=headers, timeout=5)
                response.raise_for_status()
                self.tasks_updated.emit(response.json())
            except requests.HTTPError as e:
                self.error.emit(f"Task monitor API error: {e.response.status_code}")
            except requests.RequestException as e:
                self.error.emit(f"Task monitor network error: {e}")
            
            time.sleep(5)  # Update every 5 seconds

    def stop(self) -> None:
        self.is_running = False


class LogStreamWorker(QThread):
    """
    A worker that connects to the log streaming WebSocket.
    """
    new_log_message = Signal(str)
    error = Signal(str)

    def __init__(self, parent: QThread | None = None) -> None:
        super().__init__(parent)
        self.is_running = True

    def run(self) -> None:
        """Connects to WebSocket and emits signals for new messages."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._run_client())
        except Exception as e:
            self.error.emit(f"Log stream error: {e}")
        finally:
            # Clean up the event loop
            try:
                loop.close()
            except:
                pass

    async def _run_client(self) -> None:
        uri = f"{WS_URL}/ws/logs"
        while self.is_running:
            try:
                async with websockets.connect(uri) as websocket:
                    self.error.emit("Log stream connected.")
                    while self.is_running:
                        message = await websocket.recv()
                        self.new_log_message.emit(str(message))
            except (websockets.exceptions.ConnectionClosed, OSError) as e:
                self.error.emit(f"Log stream disconnected: {e}. Reconnecting...")
                await asyncio.sleep(5)
            except Exception as e:
                self.error.emit(f"Log stream error: {e}")
                await asyncio.sleep(5)

    def stop(self) -> None:
        self.is_running = False


__all__ = ["GenericApiWorker", "HealthCheckWorker", "TaskMonitorWorker", "LogStreamWorker", "FeedbackWorker"]