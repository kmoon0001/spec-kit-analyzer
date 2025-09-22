from PyQt6.QtCore import QObject, pyqtSignal
from typing import List, Tuple

class SemanticAnalyzer:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', offline_only: bool = True):
        # Placeholder: model is not loaded
        self.model = None

    def analyze(self, doc_sentences_with_source: List[Tuple[str, str]], rubric_content: str, similarity_threshold: float = 0.5) -> list[dict]:
        # Placeholder: return empty analysis
        if not self.model:
            return [{"rule": "Error", "status": "Semantic model not loaded.", "match": "", "score": 0, "source": ""}]
        return []

class AnalysisWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, doc_sentences_with_source: List[Tuple[str, str]], rubric_content: str, offline_only: bool):
        super().__init__()
        self.doc_sentences_with_source = doc_sentences_with_source
        self.rubric_content = rubric_content
        self.offline_only = offline_only
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        # Placeholder implementation for Analysis
        self.progress.emit(100)
        final_report = "--- Semantic Rubric Analysis Report ---\n\nSemantic analysis service is disabled."
        self.finished.emit(final_report)
