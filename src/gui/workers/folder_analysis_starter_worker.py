from collections.abc import Iterable

import requests
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal as Signal

from src.config import get_settings

settings = get_settings()
API_URL = settings.paths.api_url


class FolderAnalysisStarterWorker(QObject):
    """A one-shot worker to start the folder analysis on the backend without freezing the UI.
    """

    success = Signal(str)  # Emits the task_id on success # type: ignore[attr-defined]
    error = Signal(str)  # type: ignore[attr-defined]

    def __init__(
        self,
        files: Iterable[tuple[str, tuple[str, object, str]]],
        data: dict,
        token: str,
    ):
        super().__init__()
        self.files = list(files)
        self.data = data
        self.token = token

    def run(self):
        """Sends the request to start the folder analysis and emits the result."""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(
                f"{API_URL}/analysis/analyze_folder",
                files=self.files,
                data=self.data,
                headers=headers,
                timeout=120,
            )
            response.raise_for_status()
            task_id = response.json()["task_id"]
            self.success.emit(task_id)

        except requests.exceptions.RequestException as exc:
            error_detail = str(exc)
            if exc.response is not None:
                try:
                    error_detail = exc.response.json().get("detail", str(exc))
                except requests.exceptions.JSONDecodeError:
                    pass
            self.error.emit(f"Failed to start folder analysis: {error_detail}")
        except Exception as exc:  # pragma: no cover - defensive
            self.error.emit(f"An unexpected error occurred: {exc}")
        finally:
            for _, file_tuple in self.files:
                file_tuple[1].close()
