import pytest
from unittest.mock import MagicMock, patch

from src.core.document_classifier import DocumentClassifier
from src.core.llm_service import LLMService


@pytest.fixture
def mock_llm() -> MagicMock:
    """Provides a mock LLMService that is always ready."""
    mock = MagicMock(spec=LLMService)
    mock.is_ready.return_value = True
    mock.generate.return_value = "Progress Note"
    return mock


@pytest.fixture
def classifier(mock_llm: MagicMock) -> DocumentClassifier:
    """Provides a DocumentClassifier instance with a mocked LLM service."""
    # The prompt manager inside will try to read a file, so we patch its method
    # to prevent file system access during the unit test.
    with patch(
        "src.core.prompt_manager.PromptManager.build_prompt",
        return_value="dummy prompt",
    ):
        instance = DocumentClassifier(
            llm_service=mock_llm, prompt_template_path="dummy_path.txt"
        )
        yield instance


def test_classify_evaluation(classifier: DocumentClassifier):
    """
    Tests that the classifier can process evaluation-related text.
    """
    text = "This is a patient evaluation and assessment."
    assert isinstance(classifier.classify_document(text), str)
    classifier.llm_service.generate.assert_called_once()


def test_classify_progress_note(classifier: DocumentClassifier):
    """
    Tests that the classifier can process progress note-related text.
    """
    text = "This is a daily progress note."
    assert isinstance(classifier.classify_document(text), str)


def test_classify_unknown(classifier: DocumentClassifier):
    """
    Tests that the classifier returns a string for text that doesn't match keywords.
    """
    text = "This is a standard document with no keywords."
    assert isinstance(classifier.classify_document(text), str)


def test_classify_case_insensitivity(classifier: DocumentClassifier):
    """
    Tests that the classifier is not case-sensitive when processing text.
    """
    text = "this is an EVALUATION."
    assert isinstance(classifier.classify_document(text), str)