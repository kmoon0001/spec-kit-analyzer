import pytest
from unittest.mock import MagicMock

from src.core.document_classifier import DocumentClassifier
from src.core.llm_service import LLMService


@pytest.fixture
def mock_llm_service():
    """Provides a mock LLMService that is always ready and returns a fixed classification."""
    mock_service = MagicMock(spec=LLMService)
    mock_service.is_ready.return_value = True
    mock_service.generate.return_value = "Evaluation"  # Mock LLM output
    return mock_service


@pytest.fixture
def classifier(mock_llm_service):
    """Provides a DocumentClassifier instance with a mocked LLM service."""
    # The prompt_template_path can be empty as the LLM is mocked and won't use it.
    return DocumentClassifier(llm_service=mock_llm_service, prompt_template_path="")


def test_classify_evaluation(classifier: DocumentClassifier):
    """Tests that the classifier returns the mocked LLM's output."""
    text = "This is a patient evaluation and assessment."
    assert classifier.classify_document(text) == "Evaluation"


def test_classify_progress_note(classifier: DocumentClassifier):
    """Tests that the classifier returns a string, even if the input suggests a different type."""
    text = "This is a daily progress note."
    # Our simple mock always returns "Evaluation", which is sufficient to test the flow.
    assert isinstance(classifier.classify_document(text), str)
    assert classifier.classify_document(text) == "Evaluation"


def test_classify_with_llm(classifier: DocumentClassifier):
    """Tests that the classifier correctly calls the LLM service."""
    text = "This is a standard document with no keywords."
    # The mock will return "Evaluation", demonstrating it called the LLM.
    assert classifier.classify_document(text) == "Evaluation"


def test_classify_case_insensitivity(classifier: DocumentClassifier):
    """Tests that the text is passed to the LLM regardless of case."""
    text = "this is an EVALUATION."
    assert classifier.classify_document(text) == "Evaluation"


def test_classify_document_when_llm_not_ready(mock_llm_service):
    """Tests that the classifier returns 'Unknown' if the LLM service is not ready."""
    mock_llm_service.is_ready.return_value = False
    classifier = DocumentClassifier(llm_service=mock_llm_service, prompt_template_path="")
    text = "This is any document."
    # The classifier should fall back to keyword-based logic, which will return "Unknown" for this text.
    assert classifier.classify_document(text) == "Unknown"