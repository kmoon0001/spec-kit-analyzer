import os
from typing import List, Tuple
from PySide6.QtCore import QObject, Signal as pyqtSignal
from backend.app.parsing import parse_document_content
import traceback

class DocumentWorker(QObject):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        # Placeholder implementation: simple text extraction without NLP sentence splitting.
        try:
            content_with_source = parse_document_content(self.file_path)
            if not content_with_source or (content_with_source and content_with_source[0][0].startswith("Error:")):
                error_msg = content_with_source[0][0] if content_with_source else 'Info: No text could be extracted from the document.'
                self.error.emit(error_msg)
                return

            # Simple sentence splitting by newline for placeholder
            sentences_with_source = []
            for text, source in content_with_source:
                lines = text.split('\n')
                for line in lines:
                    if line.strip():
                        sentences_with_source.append((line.strip(), source))

            self.progress.emit(100)
            self.finished.emit(sentences_with_source)
        except Exception as e:
            self.error.emit(f"Error processing file: {e}\n{traceback.format_exc()}")
