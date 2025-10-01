import sys
import os
from unittest.mock import MagicMock

# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

from core.document_classifier import DocumentClassifier


def test_classify_evaluation():
    """Tests that documents with 'evaluation' are classified correctly."""
    # Arrange
    mock_llm_service = MagicMock()
    mock_llm_service.is_ready.return_value = False  # Force fallback logic
    classifier = DocumentClassifier(llm_service=mock_llm_service, prompt_template_path="")
    text = "This is a patient evaluation and assessment."

    # Act
    result = classifier.classify_document(text)

    # Assert
    assert result == "Evaluation"


def test_classify_progress_note():
    """Tests that documents with 'progress note' are classified correctly."""
    # Arrange
    mock_llm_service = MagicMock()
    mock_llm_service.is_ready.return_value = False  # Force fallback logic
    classifier = DocumentClassifier(llm_service=mock_llm_service, prompt_template_path="")
    text = "This is a daily progress note."

    # Act
    result = classifier.classify_document(text)

    # Assert
    assert result == "Progress Note"


def test_classify_unknown():
    """Tests that documents without keywords are classified as 'Unknown'."""
    # Arrange
    mock_llm_service = MagicMock()
    mock_llm_service.is_ready.return_value = False  # Force fallback logic
    classifier = DocumentClassifier(llm_service=mock_llm_service, prompt_template_path="")
    text = "This is a standard document with no keywords."

    # Act
    result = classifier.classify_document(text)

    # Assert
    assert result == "Unknown"


def test_classify_case_insensitivity():
    """Tests that classification is case-insensitive."""
    # Arrange
    mock_llm_service = MagicMock()
    mock_llm_service.is_ready.return_value = False  # Force fallback logic
    classifier = DocumentClassifier(llm_service=mock_llm_service, prompt_template_path="")
    text = "this is an EVALUATION."

    # Act
    result = classifier.classify_document(text)

    # Assert
    assert result == "Evaluation"