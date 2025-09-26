import pytest
from unittest.mock import MagicMock, patch, call, mock_open

# Mock the config before importing the service
@pytest.fixture(autouse=True)
def mock_settings():
    with patch('src.utils.load_config') as mock_load_config:
        mock_load_config.return_value = {
            'models': {
                'generator': 'mock-generator-model',
                'summarizer': 'mock-summarizer-model'
            },
            'retrieval_settings': {
                'similarity_top_k': 3 # Changed to 3 to match the real config
            },
            'iterative_retrieval': {
                'max_iterations': 3
            }
        }
        yield

# Mock the heavy dependencies
@pytest.fixture
def mock_transformers():
    with patch('src.core.compliance_analyzer.AutoTokenizer') as mock_tokenizer, \
         patch('src.core.compliance_analyzer.AutoModelForCausalLM') as mock_causal_lm, \
         patch('src.core.compliance_analyzer.BitsAndBytesConfig') as mock_bnb_config:

        # Mock tokenizers
        mock_generator_tokenizer_inst = MagicMock()
        mock_tensor = MagicMock()
        mock_tensor.to.return_value = mock_tensor

        # The tokenizer call should return an object that has a .to() method.
        mock_tokenized_output = MagicMock()
        mock_tokenized_output.to.return_value = mock_tokenized_output
        mock_generator_tokenizer_inst.return_value = mock_tokenized_output
        mock_tokenizer.from_pretrained.return_value = mock_generator_tokenizer_inst

        # Mock models
        mock_generator_model_inst = MagicMock()
        mock_causal_lm.from_pretrained.return_value = mock_generator_model_inst
        mock_generator_model_inst.to.return_value = mock_generator_model_inst
        mock_generator_model_inst.device = 'cpu'

        # Set up decode and generate return values
        mock_generator_tokenizer_inst.decode.return_value = "mock prompt **Analysis:** final analysis"
        mock_generator_model_inst.generate.return_value = ["mock prompt **Analysis:** final analysis"]

        yield {
            "tokenizer": mock_tokenizer,
            "generator_tokenizer": mock_generator_tokenizer_inst,
            "generator_model": mock_generator_model_inst,
            "bnb_config": mock_bnb_config
        }

@pytest.fixture
def mock_guideline_service():
    mock_service = MagicMock()
    # The initial search is based on the document text, let's mock that
    mock_service.search.return_value = [
        {"text": "initial guideline text", "source": "initial_source.txt"}
    ]
    mock_service.classify_document.return_value = MagicMock()
    return mock_service

# Now import the service after mocks are set up
from src.core.compliance_analyzer import ComplianceAnalyzer as LLMComplianceAnalyzer

def test_iterative_retrieval_loop(mock_transformers, mock_guideline_service):
    """
    Tests the iterative retrieval workflow, ensuring the loop works as expected.
    """
    # Arrange: Mock the generator to first ask for a search, then provide a final answer
    mock_transformers["generator_tokenizer"].decode.side_effect = [
        "**Analysis:** [SEARCH] find more about signatures",
        '{"findings": [{"detail": "final analysis after search"}]}'
    ]

    # Mock the guideline service to return different results for each call
    # The first call is the initial search, the second is from the [SEARCH] keyword.
    mock_guideline_service.search.side_effect = [
        [{"text": "initial guideline text", "source": "initial_source.txt"}],
        [{"text": "guideline about signatures", "source": "signatures_guideline.txt"}],
    ]

    analyzer = LLMComplianceAnalyzer(guideline_service=mock_guideline_service)

    # Act
    result = analyzer.analyze_document("test document", "pt")

    # Assert
    # search should be called twice: once initially, and once for the [SEARCH] keyword
    assert mock_guideline_service.search.call_count == 2
    mock_guideline_service.search.assert_has_calls([
        call(query='test document', discipline='pt', doc_type=mock_guideline_service.classify_document.return_value.name),
        call(query='find more about signatures')
    ])

    # The final result should be the parsed JSON from the second LLM response
    assert result['findings'][0]['detail'] == "final analysis after search"

def test_multi_step_iterative_search(mock_transformers, mock_guideline_service):
    """
    Tests that the analyzer can perform multiple iterative searches.
    This replaces the outdated 'test_summarization_and_exclude_sources'.
    """
    # Arrange: Mock the generator to ask for a search twice
    mock_transformers["generator_tokenizer"].decode.side_effect = [
        "**Analysis:** [SEARCH] find more about treatment",
        "**Analysis:** [SEARCH] find more about billing",
        '{"findings": [{"detail": "final analysis"}]}'
    ]

    # Arrange: Mock the guideline service to return different results for each call
    mock_guideline_service.search.side_effect = [
        [{"text": "initial guideline"}],
        [{"text": "guideline about treatment", "source": "treatment.txt"}],
        [{"text": "guideline about billing", "source": "billing.txt"}],
    ]

    analyzer = LLMComplianceAnalyzer(guideline_service=mock_guideline_service)

    # Act
    result = analyzer.analyze_document("test document", "pt")

    # Assert
    # search should be called three times (initial + two iterative)
    assert mock_guideline_service.search.call_count == 3
    mock_guideline_service.search.assert_has_calls([
        call(query='test document', discipline='pt', doc_type=mock_guideline_service.classify_document.return_value.name),
        call(query='find more about treatment'),
        call(query='find more about billing')
    ])

    # Assert the final result
    assert result['findings'][0]['detail'] == "final analysis"
