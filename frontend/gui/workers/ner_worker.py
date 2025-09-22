from PyQt6.QtCore import QObject, pyqtSignal

class NERWorker(QObject):
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, text: str):
        super().__init__()
        self.text = text
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        # Placeholder implementation for NER
        self.progress.emit(100)
        self.finished.emit("N/A", "Clinical/Biomedical NER service is disabled.")
