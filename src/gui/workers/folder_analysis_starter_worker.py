import requests
<<<<<<< HEAD
from PyQt6.QtCore import QObject, Signal
||||||| c46cdd8
from PyQt6.QtCore import QObject, pyqtSignal
=======
from PyQt6.QtCore import QObject, pyqtSignal as Signal
>>>>>>> origin/main
from typing import List, Tuple

API_URL = "http://127.0.0.1:8000"

class FolderAnalysisStarterWorker(QObject):
    """
    A one-shot worker to start the folder analysis on the backend without freezing the UI.
    """
<<<<<<< HEAD
    success = Signal(str)  # Emits the task_id on success
    error = Signal(str)
||||||| c46cdd8
    success = pyqtSignal(str)  # Emits the task_id on success
    error = pyqtSignal(str)
=======
    success = Signal(str)  # Emits the task_id on success # type: ignore[attr-defined]
    error = Signal(str) # type: ignore[attr-defined]
>>>>>>> origin/main

    def __init__(self, files: List[Tuple], data: dict, token: str):
        super().__init__()
        self.files = files
        self.data = data
        self.token = token

    def run(self):
        """Sends the request to start the folder analysis and emits the result."""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}

            # The backend expects a specific endpoint for folder analysis
            response = requests.post(
                f"{API_URL}/analysis/analyze_folder", 
                files=self.files, 
                data=self.data, 
                headers=headers
            )
            response.raise_for_status()
            task_id = response.json()['task_id']
            self.success.emit(task_id)

        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            if e.response is not None:
                try:
                    error_detail = e.response.json().get('detail', str(e))
                except requests.exceptions.JSONDecodeError:
                    pass
            self.error.emit(f"Failed to start folder analysis: {error_detail}")
        except Exception as e:
            self.error.emit(f"An unexpected error occurred: {e}")
        finally:
            # Close the file handles that were opened to create the files list
            for _, file_tuple in self.files:
                file_tuple[1].close()
