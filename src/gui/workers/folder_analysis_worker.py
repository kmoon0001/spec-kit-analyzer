import time
import requests
from PyQt6.QtCore import QObject, pyqtSignal as Signal

API_URL = "http://127.0.0.1:8000"


class FolderAnalysisWorker(QObject):
    finished = Signal()
    error = Signal(str)
    success = Signal(str)
    progress = Signal(int)

    def __init__(self, task_id: str):
        super().__init__()
        self.task_id = task_id
        self.is_running = True

    def run(self):
        """Polls the API for the result of the folder analysis task."""
        poll_interval = 2  # seconds
        max_attempts = 150  # 5 minutes
        attempts = 0

        while self.is_running and attempts < max_attempts:
            try:
                # This worker polls the same task status endpoint
                response = requests.get(f"{API_URL}/tasks/{self.task_id}")
                response.raise_for_status()

                if response.headers.get("Content-Type") == "text/html; charset=utf-8":
                    self.success.emit(response.text)
                    self.finished.emit()
                    return

                status_data = response.json()
                status = status_data.get("status")

                if status == "processing":
                    self.progress.emit((attempts * 100) // max_attempts)
                elif status == "failed":
                    error_msg = status_data.get(
                        "error", "Unknown error during analysis."
                    )
                    self.error.emit(error_msg)
                    self.finished.emit()
                    return

            except requests.exceptions.RequestException as e:
                self.error.emit(f"Failed to connect to backend: {e}")
                self.finished.emit()
                return
            except Exception as e:
                self.error.emit(f"An unexpected error occurred: {e}")
                self.finished.emit()
                return

            time.sleep(poll_interval)
            attempts += 1

        if attempts >= max_attempts:
            self.error.emit("Analysis timed out.")

        self.finished.emit()

    def stop(self):
        self.is_running = False
