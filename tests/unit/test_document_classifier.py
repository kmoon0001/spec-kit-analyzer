import sys
import os

# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

from unittest.mock import MagicMock
import pytest
from core.document_classifier import DocumentClassifier


@pytest.fixture
def mock_llm_service():
    """Provides a mock LLM service for testing the classifier."""
    mock = MagicMock()
    mock.is_ready.return_value = True
    # Configure the mock to return a specific classification based on input
    def classify_side_effect(prompt):
        if "evaluation" in prompt.lower():
            return "Evaluation"
        if "progress note" in prompt.lower():
            return "Progress Note"
        return "Unknown"
    mock.generate_analysis.side_effect = classify_side_effect
    return mock


def test_classify_evaluation(mock_llm_service):
    # Point to the real dummy file so the prompt manager can load it.
    dummy_path = os.path.join(os.path.dirname(__file__), "dummy_prompt.txt")
    classifier = DocumentClassifier(llm_service=mock_llm_service, prompt_template_path=dummy_path)
    text = "This is a patient evaluation and assessment."
    assert classifier.classify_document(text) == "Evaluation"


def test_classify_progress_note(mock_llm_service):
    dummy_path = os.path.join(os.path.dirname(__file__), "dummy_prompt.txt")
    classifier = DocumentClassifier(llm_service=mock_llm_service, prompt_template_path=dummy_path)
    text = "This is a daily progress note."
    assert classifier.classify_document(text) == "Progress Note"


def test_classify_unknown(mock_llm_service):
    dummy_path = os.path.join(os.path.dirname(__file__), "dummy_prompt.txt")
    classifier = DocumentClassifier(llm_service=mock_llm_service, prompt_template_path=dummy_path)
    text = "This is a standard document with no keywords."
    assert classifier.classify_document(text) == "Unknown"


def test_classify_case_insensitivity(mock_llm_service):
    dummy_path = os.path.join(os.path.dirname(__file__), "dummy_prompt.txt")
    classifier = DocumentClassifier(llm_service=mock_llm_service, prompt_template_path=dummy_path)
    text = "this is an EVALUATION."
    assert classifier.classify_document(text) == "Evaluation"
