from PyQt6.QtCore import QObject, pyqtSignal
from src.gui.api_client import api_client, ApiException


class PasswordChangeWorker(QObject):
    """Worker to handle changing a user's password asynchronously using the API client."""

    success = pyqtSignal()
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(
        self,
        current_password: str,
        new_password: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.current_password = current_password
        self.new_password = new_password

    def run(self) -> None:
        """Execute the password change network request via the API client."""
        try:
            payload = {
                "current_password": self.current_password,
                "new_password": self.new_password,
            }
            api_client.post("/auth/users/change-password", data=payload)
            self.success.emit()
        except ApiException as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()