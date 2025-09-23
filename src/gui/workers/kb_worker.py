from PyQt6.QtCore import QObject, pyqtSignal
from src.knowledge_base_service import KnowledgeBaseService

class KBWorker(QObject):
    """
    A worker QObject for building the knowledge base from a document's text
    in a separate thread, preventing the UI from freezing.
    """
    finished = pyqtSignal(KnowledgeBaseService)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)

    def __init__(self, text: str, kb_service: KnowledgeBaseService):
        super().__init__()
        self.text = text
        self.kb_service = kb_service
        # Note: Cancellation is not deeply integrated into the embedding model,
        # so this is a "soft" cancellation check.
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        """
        Runs the knowledge base build process.
        """
        try:
            self.progress.emit(10, "Building knowledge base from document...")
            if self._cancel:
                self.error.emit("Knowledge base creation canceled.")
                return

            self.kb_service.build_from_text(self.text)

            if self._cancel:
                self.error.emit("Knowledge base creation canceled.")
                return

            self.progress.emit(100, "Knowledge base is ready.")
            self.finished.emit(self.kb_service)
        except Exception as e:
            self.error.emit(f"Failed to build knowledge base: {e}")
