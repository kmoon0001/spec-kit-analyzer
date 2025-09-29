import pytest
from unittest.mock import MagicMock
from src.core.document_classifier import DocumentClassifier

@pytest.fixture
def classifier():
    """Fixture to create a DocumentClassifier with a mocked LLM service."""
    mock_llm_service = MagicMock()

    # Configure the mock to return different classifications based on the prompt content
    def mock_generate_analysis(prompt: str) -> str:
        if "evaluation and assessment" in prompt.lower():
            return "Evaluation"
        if "daily progress note" in prompt.lower():
            return "Progress Note"
        return "Unknown"

    mock_llm_service.generate_analysis.side_effect = mock_generate_analysis
    mock_llm_service.is_ready.return_value = True

    # The prompt manager is also used, so we need to ensure it doesn't fail
    # We can use a dummy path since the prompt content is what matters for the mock
    classifier_instance = DocumentClassifier(
        llm_service=mock_llm_service, prompt_template_path="dummy/template.txt"
    )
    # Mock the prompt manager within the instance to simplify the test
    classifier_instance.prompt_manager = MagicMock()
    classifier_instance.prompt_manager.build_prompt.side_effect = lambda document_text: document_text

    return classifier_instance

def test_classify_evaluation(classifier: DocumentClassifier):
    """Tests that the classifier correctly identifies an evaluation note."""
    text = "This is a patient evaluation and assessment."
    assert classifier.classify_document(text) == "Evaluation"

def test_classify_progress_note(classifier: DocumentClassifier):
    """Tests that the classifier correctly identifies a progress note."""
    text = "This is a daily progress note."
    assert classifier.classify_document(text) == "Progress Note"

def test_classify_unknown(classifier: DocumentClassifier):
    """Tests that the classifier returns 'Unknown' for unrecognized text."""
    text = "This is a standard document with no keywords."
    assert classifier.classify_document(text) == "Unknown"

def test_llm_service_not_ready(classifier: DocumentClassifier):
    """Tests that the classifier returns 'Unknown' if the LLM service is not ready."""
    classifier.llm_service.is_ready.return_value = False
    text = "This is a patient evaluation and assessment."
    assert classifier.classify_document(text) == "Unknown"