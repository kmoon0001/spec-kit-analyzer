import requests
import os
from PySide6.QtCore import QObject, Signal as Signal

from src.config import get_settings

settings = get_settings()
API_URL = settings.paths.api_url


class AnalysisStarterWorker(QObject):
    """
    A one-shot worker to start the analysis on the backend without freezing the UI.
    """

    success = Signal(str)  # Emits the task_id on success
    error = Signal(str)

    def __init__(self, file_path: str, data: dict, token: str):
        super().__init__()
        self.file_path = file_path
        self.data = data
        self.token = token

    def run(self):
        """Sends the request to start the analysis and emits the result."""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            with open(self.file_path, "rb") as f:
                files = {"file": (os.path.basename(self.file_path), f)}
                response = requests.post(
                    f"{API_URL}/analysis/analyze",
                    files=files,
                    data=self.data,
                    headers=headers,
                )
            response.raise_for_status()
            task_id = response.json()["task_id"]
            self.success.emit(task_id)

        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            if e.response is not None:
                try:
                    error_detail = e.response.json().get("detail", str(e))
                except requests.exceptions.JSONDecodeError:
                    pass
            self.error.emit(f"Failed to start analysis: {error_detail}")
        except Exception as e:
            self.error.emit(f"An unexpected error occurred: {e}")
