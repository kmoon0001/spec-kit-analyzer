
import requests
from PySide6.QtCore import QObject, Signal


class ApiAnalysisWorker(QObject):
    """A QThread worker for calling the backend analysis API."""

    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, file_path: str, api_url: str = "http://127.0.0.1:8004/analyze", token: str = None):
        super().__init__()
        self.file_path = file_path
        self.api_url = api_url
        self.token = token

    def run(self):
        """Sends the file to the backend and emits the result."""
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            
            with open(self.file_path, "rb") as f:
                files = {"file": (self.file_path, f)}
                response = requests.post(self.api_url, files=files, headers=headers, timeout=120)

            response.raise_for_status()

            result_data = response.json()
            self.finished.emit(result_data)

        except requests.exceptions.RequestException as e:
            self.error.emit(f"API request failed: {e}")
        except (FileNotFoundError, PermissionError, OSError) as e:
            self.error.emit(f"An unexpected error occurred: {e}")
