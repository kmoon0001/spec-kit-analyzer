
import requests
from PySide6.QtCore import QObject, Signal, Slot
from requests.exceptions import HTTPError

from src.config import get_settings

settings = get_settings()
API_URL = settings.paths.api_url


class RubricApiWorker(QObject):
    """Handles CRUD operations for rubrics asynchronously."""

    success = Signal(object)
    error = Signal(str)

    def __init__(self, token: str):
        super().__init__()
        self.token = token

    def _get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def _handle_request(self, method: str, endpoint: str, json_data: dict | None = None):
        try:
            url = f"{API_URL}{endpoint}"
            response = requests.request(method, url, headers=self._get_headers(), json=json_data, timeout=15)
            response.raise_for_status()
            self.success.emit(response.json() if response.content else None)
        except requests.RequestException as e:
            error_msg = str(e)
            if e.response is not None:
                try:
                    error_msg = e.response.json().get("detail", error_msg)
                except ValueError:
                    pass
            self.error.emit(f"API Error: {error_msg}")
        except (ConnectionError, TimeoutError, HTTPError) as e:
            self.error.emit(f"An unexpected error occurred: {e}")

    @Slot()
    def get_all(self):
        self._handle_request("GET", "/rubrics/")

    @Slot(dict)
    def create(self, data: dict):
        self._handle_request("POST", "/rubrics/", json_data=data)

    @Slot(str, dict)
    def update(self, rubric_id: str, data: dict):
        self._handle_request("PUT", f"/rubrics/{rubric_id}", json_data=data)

    @Slot(str)
    def delete(self, rubric_id: str):
        self._handle_request("DELETE", f"/rubrics/{rubric_id}")
