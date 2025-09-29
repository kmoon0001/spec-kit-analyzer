import requests
from PyQt6.QtCore import QObject, pyqtSignal

from src.config import get_settings

settings = get_settings()
API_URL = settings.api_url


class PasswordChangeWorker(QObject):
    """Worker to handle changing a user's password asynchronously."""

    success = pyqtSignal()
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(
        self,
        token: str,
        current_password: str,
        new_password: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.token = token
        self.current_password = current_password
        self.new_password = new_password
        self._is_running = True

    def run(self) -> None:
        """Execute the password change network request."""
        try:
            if not self._is_running:
                return

            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "current_password": self.current_password,
                "new_password": self.new_password,
            }
            response = requests.post(
                f"{API_URL}/auth/users/change-password",
                json=payload,
                headers=headers,
                timeout=15,  # Add a timeout
            )
            response.raise_for_status()
            self.success.emit()
        except requests.exceptions.RequestException as e:
            detail = "An unknown error occurred."
            if e.response is not None:
                try:
                    detail = e.response.json().get("detail", str(e))
                except requests.exceptions.JSONDecodeError:
                    detail = e.response.text
            else:
                detail = str(e)
            self.error.emit(detail)
        finally:
            self.finished.emit()

    def stop(self) -> None:
        """Stop the worker."""
        self._is_running = False