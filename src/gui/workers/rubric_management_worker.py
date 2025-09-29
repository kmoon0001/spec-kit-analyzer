from PyQt6.QtCore import QObject, pyqtSignal
from typing import Any, Dict, List
from src.gui.api_client import api_client, ApiException

class RubricLoaderWorker(QObject):
    """Worker to load all rubrics from the API."""
    success = pyqtSignal(list)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def run(self):
        try:
            rubrics = api_client.get("/rubrics/")
            self.success.emit(rubrics or [])
        except ApiException as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

class RubricAdderWorker(QObject):
    """Worker to add a new rubric via the API."""
    success = pyqtSignal()
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, data: Dict[str, Any]):
        super().__init__()
        self.data = data

    def run(self):
        try:
            api_client.post("/rubrics/", data=self.data)
            self.success.emit()
        except ApiException as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

class RubricEditorWorker(QObject):
    """Worker to update an existing rubric via the API."""
    success = pyqtSignal()
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, rubric_id: int, data: Dict[str, Any]):
        super().__init__()
        self.rubric_id = rubric_id
        self.data = data

    def run(self):
        try:
            api_client.put(f"/rubrics/{self.rubric_id}", data=self.data)
            self.success.emit()
        except ApiException as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

class RubricDeleterWorker(QObject):
    """Worker to delete a rubric via the API."""
    success = pyqtSignal()
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, rubric_id: int):
        super().__init__()
        self.rubric_id = rubric_id

    def run(self):
        try:
            api_client.delete(f"/rubrics/{self.rubric_id}")
            self.success.emit()
        except ApiException as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()