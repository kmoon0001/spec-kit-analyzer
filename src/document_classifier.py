from enum import Enum, auto

class DocumentType(Enum):
    EVALUATION = auto()
    PROGRESS_NOTE = auto()
    UNKNOWN = auto()

class DocumentClassifier:
    """
    A simple classifier to determine the type of a clinical document.
    """
    @staticmethod
    def classify(text: str) -> DocumentType:
        """
        Classifies the document text based on keywords.

        Args:
            text: The text of the document.

        Returns:
            The classified document type.
        """
        text_lower = text.lower()
        if "evaluation" in text_lower or "assessment" in text_lower:
            return DocumentType.EVALUATION
        if "progress note" in text_lower:
            return DocumentType.PROGRESS_NOTE
        return DocumentType.UNKNOWN
