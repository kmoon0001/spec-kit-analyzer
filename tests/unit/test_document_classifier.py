import pytest
from unittest.mock import MagicMock
from src.core.document_classifier import DocumentClassifier
from src.core.llm_service import LLMService

def mock_llm_service():
    """Provides a mock LLMService."""
    mock_service = MagicMock(spec=LLMService)
    mock_service.is_ready.return_value = True
    mock_service.generate.return_value = "Evaluation"
    return mock_service

def test_classify_evaluation():
    mock_llm = mock_llm_service()
    classifier = DocumentClassifier(llm_service=mock_llm, prompt_template_path="")
    text = "This is a patient evaluation and assessment."
    assert classifier.classify_document(text) == "Evaluation"

def test_classify_progress_note():
    mock_llm = mock_llm_service()
    mock_llm.generate.return_value = "Progress Note"
    classifier = DocumentClassifier(llm_service=mock_llm, prompt_template_path="")
    text = "This is a daily progress note."
    assert classifier.classify_document(text) == "Progress Note"

def test_classify_unknown():
    mock_llm = mock_llm_service()
    mock_llm.is_ready.return_value = False
    classifier = DocumentClassifier(llm_service=mock_llm, prompt_template_path="")
    text = "This is a standard document with no keywords."
    assert isinstance(classifier.classify_document(text), str)

def test_classify_case_insensitivity():
    mock_llm = mock_llm_service()
    classifier = DocumentClassifier(llm_service=mock_llm, prompt_template_path="")
    text = "this is an EVALUATION."
    assert classifier.classify_document(text) == "Evaluation"