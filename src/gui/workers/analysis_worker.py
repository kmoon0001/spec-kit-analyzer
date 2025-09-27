import time
import requests
from PyQt6.QtCore import QObject, pyqtSignal as Signal

from src.config import get_settings

settings = get_settings()
API_URL = settings.api_url


class AnalysisWorker(QObject):
    finished = Signal()
    error = Signal(str)
    success = Signal(str)
    progress = Signal(int)

    def __init__(self, task_id: str):
        super().__init__()
        self.task_id = task_id

    def run(self):
        try:
            while True:
                response = requests.get(f"{API_URL}/tasks/{self.task_id}")
                response.raise_for_status()
                task = response.json()

                if task["status"] == "completed":
                    self.success.emit(task["result"])
                    break
                if task["status"] == "failed":
                    self.error.emit(task["error"])
                    break
                self.progress.emit(50)  # Update with a more meaningful progress
                time.sleep(1)
        except Exception as e:
            self.error.emit(f"Failed to connect to backend or perform analysis:\n{e}")
        finally:
            self.finished.emit()
