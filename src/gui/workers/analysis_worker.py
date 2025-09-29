import time
from typing import Any, Dict

import requests
from PyQt6.QtCore import QObject, pyqtSignal as Signal

from src.config import get_settings

settings = get_settings()
API_URL = settings.api_url


class AnalysisWorker(QObject):
    finished = Signal()
    error = Signal(str)
    success = Signal(object)
    progress = Signal(int)

    def __init__(self, task_id: str):
        super().__init__()
        self.task_id = task_id
        self._is_running = True

    def stop(self) -> None:
        """Request the polling loop to stop."""
        self._is_running = False

    def run(self) -> None:
        try:
            while self._is_running:
                response = requests.get(f"{API_URL}/tasks/{self.task_id}", timeout=15)
                response.raise_for_status()
                task: Dict[str, Any] = response.json()

                status = task.get("status")
                if status == "completed":
                    self.success.emit(task.get("result"))
                    break
                if status == "failed":
                    self.error.emit(task.get("error", "Analysis failed."))
                    break

                reported_progress = int(task.get("progress", 50))
                self.progress.emit(max(0, min(100, reported_progress)))
                time.sleep(1)
        except requests.RequestException as exc:
            self.error.emit(f"Failed to connect to backend or perform analysis:\n{exc}")
        except Exception as exc:  # pragma: no cover - defensive
            self.error.emit(f"Unexpected analysis error: {exc}")
        finally:
            self._is_running = False
            self.finished.emit()
