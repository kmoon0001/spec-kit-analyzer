"""
A generic QThread worker for making simple API GET requests.
"""
from __future__ import annotations

from typing import Any

import requests
from PySide6.QtCore import QThread, Signal

from src.config import get_settings

SETTINGS = get_settings()
API_URL = SETTINGS.paths.api_url


class GenericApiWorker(QThread):
    """
    A worker that fetches data from a specified API endpoint.
    """

    success = Signal(object)
    error = Signal(str)

    def __init__(self, endpoint: str, parent: QThread | None = None) -> None:
        super().__init__(parent)
        self.endpoint = endpoint
        self.is_running = True

    def run(self) -> None:
        """Fetches data from the API and emits success or error signal."""
        try:
            url = f"{API_URL}{self.endpoint}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.success.emit(data)
        except requests.HTTPError as e:
            self.error.emit(
                f"API error for {self.endpoint}: {e.response.status_code} {e.response.reason}"
            )
        except requests.RequestException as e:
            self.error.emit(f"Network error while fetching {self.endpoint}: {e}")


__all__ = ["GenericApiWorker"]