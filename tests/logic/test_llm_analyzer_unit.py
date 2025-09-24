import pytest
from unittest.mock import MagicMock, patch, call

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
                'similarity_top_k': 1
            },
            'iterative_retrieval': {
                'max_iterations': 2
            }
        }
        yield

# Mock the heavy dependencies
@pytest.fixture
def mock_transformers():
    with patch('src.core.llm_analyzer.AutoTokenizer') as mock_tokenizer, \
         patch('src.core.llm_analyzer.AutoModelForCausalLM') as mock_causal_lm, \
         patch('src.core.llm_analyzer.AutoModelForSeq2SeqLM') as mock_seq2seq_lm:

        # Mock tokenizers
        mock_generator_tokenizer_inst = MagicMock()
        mock_summarizer_tokenizer_inst = MagicMock()
        mock_tensor = MagicMock()
        mock_tensor.to.return_value = mock_tensor
        mock_generator_tokenizer_inst.return_value = {"input_ids": mock_tensor}
        mock_summarizer_tokenizer_inst.return_value = {"input_ids": mock_tensor}

        # Side effect to return the correct tokenizer for each model
        mock_tokenizer.from_pretrained.side_effect = [mock_generator_tokenizer_inst, mock_summarizer_tokenizer_inst]

        # Mock models
        mock_generator_model_inst = MagicMock()
        mock_summarizer_model_inst = MagicMock()

        mock_causal_lm.from_pretrained.return_value = mock_generator_model_inst
        mock_seq2seq_lm.from_pretrained.return_value = mock_summarizer_model_inst

        # Set up decode and generate return values
        mock_generator_tokenizer_inst.decode.return_value = "mock prompt **Analysis:** final analysis"
        mock_summarizer_tokenizer_inst.decode.return_value = "summarized context"

        mock_generator_model_inst.generate.return_value = ["mock prompt **Analysis:** final analysis"]
        mock_summarizer_model_inst.generate.return_value = ["summarized context"]

        yield {
            "tokenizer": mock_tokenizer,
            "generator_tokenizer": mock_generator_tokenizer_inst,
            "summarizer_tokenizer": mock_summarizer_tokenizer_inst,
            "generator_model": mock_generator_model_inst,
            "summarizer_model": mock_summarizer_model_inst
        }

@pytest.fixture
def mock_guideline_service():
    mock_service = MagicMock()
    mock_service.search.return_value = [
        {"text": "initial guideline text", "source": "initial_source.txt"}
    ]
    return mock_service

# Now import the service after mocks are set up
from src.core.llm_analyzer import LLMComplianceAnalyzer

def test_analyze_document_iterative(mock_transformers, mock_guideline_service):
    """
    Tests the iterative retrieval workflow.
    """
    # Arrange: Mock the generator to first ask for a search, then provide an answer
    mock_transformers["generator_tokenizer"].decode.side_effect = [
        "**Analysis:** [SEARCH] find more about signatures",
        "**Analysis:** final analysis after search"
    ]

    # Arrange: Mock the guideline service to return different results for the second call
    mock_guideline_service.search.side_effect = [
        [{"text": "initial guideline text", "source": "initial_source.txt"}],
        [{"text": "new guideline text", "source": "new_source.txt"}]
    ]

    analyzer = LLMComplianceAnalyzer(guideline_service=mock_guideline_service)

    # Act
    result = analyzer.analyze_document("test document")

    # Assert
    assert mock_guideline_service.search.call_count == 2
    mock_guideline_service.search.assert_has_calls([
        call(query='test document', top_k=1, exclude_sources=[]),
        call(query='find more about signatures', top_k=1, exclude_sources=['initial_source.txt'])
    ])
    assert result == "final analysis after search"

def test_analyze_document_summarization(mock_transformers, mock_guideline_service):
    """
    Tests that the summarization step is called and its output is used.
    """
    # Arrange
    mock_guideline_service.search.return_value = [
        {"text": "guideline text", "source": "guideline_source.txt"}
    ]
    analyzer = LLMComplianceAnalyzer(guideline_service=mock_guideline_service)

    # Act
    analyzer.analyze_document("test document")

    # Assert
    # Check that summarizer was called
    assert mock_transformers["summarizer_model"].generate.call_count == 1

    # Check that the generator prompt contains the summarized context
    final_prompt = mock_transformers["generator_tokenizer"].call_args[0][0]
    assert "summarized context" in final_prompt
