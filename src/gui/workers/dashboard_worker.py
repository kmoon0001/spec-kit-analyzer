import requests
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal as Signal
from requests.exceptions import HTTPError

from src.config import get_settings

settings = get_settings()
API_URL = settings.paths.api_url


class DashboardWorker(QObject):
    """A worker to fetch all necessary dashboard data from the API."""

    success = Signal(dict)  # Emits a dictionary with 'reports' and 'summary'
    error = Signal(str)
    finished = Signal()

    def __init__(self, token: str):
        super().__init__()
        self.token = token

    def run(self):
        """Fetches all dashboard data and emits the result."""
        try:
            if not self.token:
                self.error.emit("Authentication token not provided.")
                return

            headers = {"Authorization": f"Bearer {self.token}"}

            # 1. Fetch historical reports
            reports_response = requests.get(
                f"{API_URL}/dashboard/reports",
                headers=headers)
            reports_response.raise_for_status()
            reports_data = reports_response.json()

            # 2. Fetch findings summary
            summary_response = requests.get(
                f"{API_URL}/dashboard/findings-summary",
                headers=headers)
            summary_response.raise_for_status()
            summary_data = summary_response.json()

            # 3. Emit both datasets in a single dictionary
            self.success.emit({"reports": reports_data, "summary": summary_data})

        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            if e.response is not None:
                try:
                    error_detail = e.response.json().get("detail", str(e))
                except requests.exceptions.JSONDecodeError:
                    pass
            self.error.emit(f"Failed to fetch dashboard data: {error_detail}")
        except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
            self.error.emit(f"An unexpected error occurred: {e}")
        finally:
            self.finished.emit()
