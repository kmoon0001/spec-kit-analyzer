import pytest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure the src directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ner_service import NERService
from src.context_service import ContextService

@pytest.fixture
def mock_context_service():
    """Fixture for a mock ContextService."""
    mock_service = MagicMock(spec=ContextService)
    mock_service.is_ready.return_value = True
    mock_service.classify_sentence.return_value = "Test Context"
    return mock_service

# We only need to patch the 'from_pretrained' methods to prevent downloads.
# This allows the NERService to initialize without crashing, even though pipeline creation will fail internally.
@patch('src.ner_service.AutoModelForTokenClassification.from_pretrained')
@patch('src.ner_service.AutoTokenizer.from_pretrained')
def test_ner_service_extraction(mock_tokenizer, mock_model, mock_context_service):
    """
    Tests the NERService's entity extraction capability by bypassing the real pipeline creation.
    """
    # 1. Arrange
    # Let the NERService __init__ run. It will try to create a pipeline and fail gracefully
    # inside its own try/except block. We don't need to mock the pipeline function itself.
    mock_tokenizer.return_value = MagicMock()
    mock_model.return_value = MagicMock() # A simple mock is enough now

    model_configs = {"mock_model": "mock/model-name"}
    ner_service = NERService(model_configs, context_service=mock_context_service)

    # At this point, ner_service.pipes is empty because the real pipeline call failed.
    assert not ner_service.is_ready()

    # 2. Manually inject a mock pipeline into the service instance.
    # This is the object that will be called by extract_entities.
    mock_pipeline_instance = MagicMock()
    mock_pipeline_instance.return_value = [
        {'entity_group': 'DIAGNOSIS', 'score': 0.99, 'word': 'headache', 'start': 12, 'end': 20}
    ]
    ner_service.pipes["mock_model"] = mock_pipeline_instance

    # Sanity check that the service is now considered ready.
    assert ner_service.is_ready()

    # 3. Act
    text = "Patient has a headache."
    sentences = ["Patient has a headache."]
    results = ner_service.extract_entities(text, sentences)

    # 4. Assert
    assert "mock_model" in results
    assert len(results["mock_model"]) == 1

    entity = results["mock_model"][0]
    assert entity.text == "headache"
    assert entity.label == "DIAGNOSIS"
    assert entity.context == "Test Context"

    # Check that our mock pipeline was called with the correct text
    mock_pipeline_instance.assert_called_once_with(text)

    # Check that the context service was called
    mock_context_service.classify_sentence.assert_called_once_with("Patient has a headache.")
