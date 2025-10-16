import requests
from PySide6.QtCore import QObject, Signal, Slot
from requests.exceptions import HTTPError

from src.config import get_settings

settings = get_settings()
API_URL = settings.paths.api_url


class ChatWorker(QObject):
    """Worker to handle AI chat requests asynchronously."""

    success = Signal(str)
    error = Signal(str)
    finished = Signal()

    def __init__(self, history: list[dict[str, str]], token: str):
        super().__init__()
        self.history = history
        self.token = token
        self._should_stop = False

    @Slot()
    def run(self):
        """Send chat message and emit result."""
        if self._should_stop:
            return

        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {"history": self.history}

            response = requests.post(f"{API_URL}/chat", json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            if not self._should_stop:
                self.success.emit(response.json().get("response", "No valid response from AI."))
        except requests.exceptions.RequestException as e:
            if not self._should_stop:
                if e.response is not None:
                    try:
                        detail = e.response.json().get("detail", str(e))
                        self.error.emit(f"API Error: {detail}")
                    except ValueError:
                        self.error.emit(f"API Error: {e.response.status_code} {e.response.reason}")
                else:
                    self.error.emit(f"Failed to connect to the AI service: {e}")
        except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
            if not self._should_stop:
                self.error.emit(f"An unexpected error occurred: {e}")
        finally:
            self.finished.emit()

    def stop(self) -> None:
        """Stop the worker gracefully."""
        self._should_stop = True
