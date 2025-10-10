
import os
import time

import requests
from PySide6.QtCore import QObject, Signal, Slot

from src.config import get_settings

settings = get_settings()
API_URL = settings.paths.api_url

class BatchProcessorWorker(QObject):
    """Processes a list of files by sending them for analysis one by one."""

    progress = Signal(int, int, str)  # current, total, filename
    file_completed = Signal(str, str)  # filename, status
    finished = Signal()
    error = Signal(str)

    def __init__(self, file_paths: list[str], token: str, analysis_data: dict):
        super().__init__()
        self.file_paths = file_paths
        self.token = token
        self.analysis_data = analysis_data
        self._is_running = True

    @Slot()
    def run(self):
        """Iterate through files, analyze them, and report progress."""
        total_files = len(self.file_paths)
        headers = {"Authorization": f"Bearer {self.token}"}

        for i, file_path in enumerate(self.file_paths):
            if not self._is_running:
                break

            filename = os.path.basename(file_path)
            self.progress.emit(i, total_files, f"Starting: {filename}")

            try:
                # 1. Start Analysis (send file content)
                with open(file_path, "rb") as f:
                    files = {"file": (filename, f)}
                    response = requests.post(
                        f"{API_URL}/analysis/analyze",
                        files=files,
                        data=self.analysis_data,
                        headers=headers,
                        timeout=30,
                    )
                    response.raise_for_status()
                    task_id = response.json()["task_id"]

                # 2. Poll for results
                self.progress.emit(i, total_files, f"Processing: {filename}")
                while self._is_running:
                    poll_response = requests.get(f"{API_URL}/analysis/status/{task_id}", headers=headers, timeout=10)
                    poll_response.raise_for_status()
                    status_data = poll_response.json()

                    if status_data["status"] == "completed":
                        self.file_completed.emit(filename, "Completed")
                        break
                    elif status_data["status"] == "failed":
                        error_msg = status_data.get("error", "Unknown error")
                        self.file_completed.emit(filename, f"Failed: {error_msg}")
                        break

                    time.sleep(2) # Wait before polling again

            except requests.RequestException as e:
                error_detail = str(e)
                if e.response is not None:
                    try:
                        error_detail = e.response.json().get("detail", str(e))
                    except ValueError:
                        pass
                self.file_completed.emit(filename, f"Error: {error_detail}")
            except Exception as e:
                self.file_completed.emit(filename, f"Error: {e!s}")

        self.finished.emit()

    def stop(self):
        self._is_running = False
