import sys
import os
import pytest
from unittest.mock import MagicMock

# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

from core.document_classifier import DocumentClassifier

@pytest.fixture
def mock_llm_service(mocker):
    """Fixture to create a mock LLMService."""
    mock = MagicMock()
    mock.is_ready.return_value = True
    return mock

@pytest.fixture
def dummy_prompt_path(tmp_path):
    """Fixture to create a dummy prompt template file."""
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("Classify: {document_text}")
    return str(prompt_file)

def test_classify_evaluation(mock_llm_service, dummy_prompt_path):
    """Test that the classifier correctly identifies an 'Evaluation' document."""
    mock_llm_service.generate_analysis.return_value = "Evaluation"
    classifier = DocumentClassifier(
        llm_service=mock_llm_service, prompt_template_path=dummy_prompt_path
    )
    text = "This is a patient evaluation and assessment."

    result = classifier.classify_document(text)

    assert result == "Evaluation"
    mock_llm_service.generate_analysis.assert_called_once()

def test_classify_progress_note(mock_llm_service, dummy_prompt_path):
    """Test that the classifier correctly identifies a 'Progress Note' document."""
    mock_llm_service.generate_analysis.return_value = "Progress Note"
    classifier = DocumentClassifier(
        llm_service=mock_llm_service, prompt_template_path=dummy_prompt_path
    )
    text = "This is a daily progress note."

    result = classifier.classify_document(text)

    assert result == "Progress Note"
    mock_llm_service.generate_analysis.assert_called_once()

def test_classify_unknown_on_invalid_llm_output(mock_llm_service, dummy_prompt_path):
    """Test that the classifier returns 'Unknown' if the LLM provides an invalid type."""
    mock_llm_service.generate_analysis.return_value = "Some Invalid Type"
    classifier = DocumentClassifier(
        llm_service=mock_llm_service, prompt_template_path=dummy_prompt_path
    )
    text = "This is a standard document with no keywords."

    result = classifier.classify_document(text)

    assert result == "Unknown"
    mock_llm_service.generate_analysis.assert_called_once()

def test_classify_unknown_when_llm_not_ready(mock_llm_service, dummy_prompt_path):
    """Test that the classifier returns 'Unknown' when the LLM service is not ready."""
    mock_llm_service.is_ready.return_value = False
    classifier = DocumentClassifier(
        llm_service=mock_llm_service, prompt_template_path=dummy_prompt_path
    )
    text = "This document text doesn't matter for this test."

    result = classifier.classify_document(text)

    assert result == "Unknown"
    mock_llm_service.generate_analysis.assert_not_called()