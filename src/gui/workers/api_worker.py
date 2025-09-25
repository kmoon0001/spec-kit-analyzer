import requests
from PyQt6.QtCore import QObject, pyqtSignal

class ApiAnalysisWorker(QObject):
    """
    A QThread worker for calling the backend analysis API.
    """
    finished = pyqtSignal(dict) 
    error = pyqtSignal(str)

    def __init__(self, file_path: str, api_url: str = "http://127.0.0.1:8000/analyze"):
        super().__init__()
        self.file_path = file_path
        self.api_url = api_url

    def run(self):
        """
        Sends the file to the backend and emits the result.
        """
        try:
            with open(self.file_path, 'rb') as f:
                files = {'file': (self.file_path, f)}
                response = requests.post(self.api_url, files=files, timeout=120)

            response.raise_for_status()

            result_data = response.json()
            self.finished.emit(result_data)

        except requests.exceptions.RequestException as e:
            self.error.emit(f"API request failed: {e}")
        except Exception as e:
            self.error.emit(f"An unexpected error occurred: {e}")
