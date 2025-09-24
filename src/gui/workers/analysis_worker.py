import os
import requests
from PySide6.QtCore import QObject, Signal

API_URL = "http://127.0.0.1:8000"

class AnalysisWorker(QObject):
    finished = Signal()
    error = Signal(str)
    success = Signal(str) 

    def __init__(self, file_path, data):
        super().__init__()
        self.file_path = file_path
        self.data = data

    def run(self):
        try:
            with open(self.file_path, 'rb') as f:
                files = {'file': (os.path.basename(self.file_path), f)}
                response = requests.post(f"{API_URL}/analyze", files=files, data=self.data)

            if response.status_code == 200:
                self.success.emit(response.text)
            else:
                error_text = f"Error from backend: {response.status_code}\n\n{response.text}"
                self.error.emit(error_text)
        except Exception as e:
            self.error.emit(f"Failed to connect to backend or perform analysis:\n{e}")
        finally:
            self.finished.emit()
