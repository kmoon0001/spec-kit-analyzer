import time
from typing import Any

import requests
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal as Signal

from src.config import get_settings

settings = get_settings()
API_URL = settings.paths.api_url


class FolderAnalysisWorker(QObject):
    finished = Signal()  # type: ignore[attr-defined]
    error = Signal(str)  # type: ignore[attr-defined]
    success = Signal(object)  # type: ignore[attr-defined]
    progress = Signal(int)  # type: ignore[attr-defined]

    def __init__(self, task_id: str):
        super().__init__()
        self.task_id = task_id
        self.is_running = True

    def stop(self) -> None:
        self.is_running = False

    def run(self):
        """Poll the API for the result of the folder analysis task."""
        poll_interval = 2  # seconds
        max_attempts = 150  # 5 minutes
        attempts = 0

        while self.is_running and attempts < max_attempts:
            try:
                response = requests.get(
                    f"{API_URL}/tasks/{self.task_id}",
                    timeout=15,
                )
                response.raise_for_status()

                if response.headers.get("Content-Type", "").startswith("text/html"):
                    self.success.emit(response.text)
                    self.finished.emit()
                    return

                status_data: dict[str, Any] = response.json()
                status = status_data.get("status")

                if status == "processing":
                    reported_progress = int(
                        status_data.get("progress", attempts * 100 // max_attempts),
                    )
                    self.progress.emit(max(0, min(100, reported_progress)))
                elif status == "failed":
                    error_msg = status_data.get(
                        "error", "Unknown error during analysis.",
                    )
                    self.error.emit(error_msg)
                    self.finished.emit()
                    return
                elif status == "completed":
                    self.success.emit(status_data.get("result"))
                    self.finished.emit()
                    return

            except requests.RequestException as exc:
                self.error.emit(f"Failed to connect to backend: {exc}")
                self.finished.emit()
                return
            except Exception as exc:  # pragma: no cover - defensive
                self.error.emit(f"An unexpected error occurred: {exc}")
                self.finished.emit()
                return

            time.sleep(poll_interval)
            attempts += 1

        if attempts >= max_attempts:
            self.error.emit("Analysis timed out.")

        self.finished.emit()
