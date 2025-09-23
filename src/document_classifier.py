from enum import Enum

class DocumentType(Enum):
    EVALUATION = "Evaluation"
    PROGRESS_NOTE = "Progress Note"

class DocumentClassifier:
    def classify(self, text: str) -> DocumentType | None:
        """
        Classifies the document type based on keywords.
        """
        text_lower = text.lower()
        if "evaluation" in text_lower or "assessment" in text_lower:
            return DocumentType.EVALUATION
        if "progress note" in text_lower:
            return DocumentType.PROGRESS_NOTE
        return None
