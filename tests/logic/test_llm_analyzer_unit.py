import pytest
from unittest.mock import MagicMock, patch

# Mock the config before importing the service
@pytest.fixture(autouse=True)
def mock_settings():
    with patch('src.utils.load_config') as mock_load_config:
        mock_load_config.return_value = {
            'models': {
                'generator': 'mock-generator-model'
            },
            'retrieval_settings': {
                'similarity_top_k': 1
            }
        }
        yield

# Mock the heavy dependencies
@pytest.fixture
def mock_transformers():
    with patch('src.core.llm_analyzer.AutoTokenizer') as mock_tokenizer, \
         patch('src.core.llm_analyzer.AutoModelForCausalLM') as mock_model:

        # Mock tokenizer
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.return_value = {"input_ids": "mock_input_ids"}
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance

        # Mock model
        mock_model_instance = MagicMock()
        # Simulate a generated output that includes the original prompt
        mock_model_instance.generate.return_value = ["mock prompt **Analysis:** mock analysis result"]
        mock_tokenizer_instance.decode.return_value = "mock prompt **Analysis:** mock analysis result"
        mock_model.from_pretrained.return_value = mock_model_instance

        yield mock_tokenizer, mock_model

@pytest.fixture
def mock_guideline_service():
    mock_service = MagicMock()
    mock_service.search.return_value = [
        {"text": "guideline text", "source": "guideline_source.txt"}
    ]
    return mock_service

# Now import the service after mocks are set up
from src.core.llm_analyzer import LLMComplianceAnalyzer

def test_analyze_document(mock_transformers, mock_guideline_service):
    """
    Tests the full analyze_document workflow with mocked dependencies.
    """
    # Initialize the analyzer with the mocked guideline service
    analyzer = LLMComplianceAnalyzer(guideline_service=mock_guideline_service)

    document_text = "This is a test document."
    result = analyzer.analyze_document(document_text)

    # 1. Check if the guideline service was called
    mock_guideline_service.search.assert_called_once()

    # 2. Check if the prompt was constructed and passed to the model
    mock_tokenizer, mock_model = mock_transformers
    mock_model_instance = mock_model.from_pretrained()

    # Check that generate was called
    mock_model_instance.generate.assert_called_once()

    # 3. Check if the result is correctly parsed from the model's output
    assert result == "mock analysis result"
