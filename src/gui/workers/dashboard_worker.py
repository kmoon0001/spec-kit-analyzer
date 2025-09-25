import requests
from PyQt6.QtCore import QObject, Signal
from typing import List, Dict, Any

API_URL = "http://127.0.0.1:8000"

class DashboardWorker(QObject):
    """
    A worker to fetch historical report data from the API in the background.
    """
    success = Signal(list)
    error = Signal(str)

    def __init__(self, token: str):
        super().__init__()
        self.token = token

    def run(self):
        """
        Fetches the report data and emits the result.
        """
        if not self.token:
            self.error.emit("Authentication token not provided.")
            return

        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{API_URL}/dashboard/reports", headers=headers)
            response.raise_for_status() # Raise an exception for bad status codes
            
            reports_data = response.json()
            self.success.emit(reports_data)

        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            if e.response is not None:
                try:
                    error_detail = e.response.json().get('detail', str(e))
                except requests.exceptions.JSONDecodeError:
                    pass # Keep the original error string
            self.error.emit(f"Failed to fetch dashboard data: {error_detail}")
        except Exception as e:
            self.error.emit(f"An unexpected error occurred: {e}")
