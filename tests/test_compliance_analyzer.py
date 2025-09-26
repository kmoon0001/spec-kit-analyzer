import pytest
from unittest.mock import MagicMock, patch

# Import the class we are testing
from src.core.llm_analyzer import LLMComplianceAnalyzer
from src.core.llm_service import LLMService
from src.core.prompt_manager import PromptManager

# --- Mocks and Fixtures ---

@pytest.fixture
def mock_prompt_manager():
    """A mock for the PromptManager."""
    pm = MagicMock(spec=PromptManager)
    pm.build_prompt.return_value = "This is a formatted prompt."
    return pm

@pytest.fixture
def llm_service_with_mocked_model():
    """
    This fixture is the key to preventing the model download.
    It patches the 'from_pretrained' method in the ctransformers library
    so that it returns a mock object instead of downloading a real model.
    """
    # Patch the method that downloads the model
    with patch('ctransformers.AutoModelForCausalLM.from_pretrained') as mock_from_pretrained:
        # The mock model needs to be callable to simulate generation
        mock_llm = MagicMock()
        mock_llm.return_value = '{"findings": [{"text": "Mocked LLM analysis."}]}'
        mock_from_pretrained.return_value = mock_llm

        # Now, instantiate the real LLMService. It will use the mocked download method.
        llm_service = LLMService(
            model_repo_id="TheBloke/Fake-Model-GGUF", # Fake model
            model_filename="fake-model.gguf",
            llm_settings={'generation_params': {}}
        )
        # We can also mock the generate_analysis method directly if we want more control
        llm_service.generate_analysis = MagicMock(return_value='{"findings": [{"text": "Mocked LLM analysis."}]}')
        yield llm_service

# --- Tests ---

def test_llm_compliance_analyzer_initialization(llm_service_with_mocked_model, mock_prompt_manager):
    """
    Tests that the LLMComplianceAnalyzer correctly initializes with its dependencies.
    """
    # Act
    analyzer = LLMComplianceAnalyzer(
        llm_service=llm_service_with_mocked_model,
        prompt_manager=mock_prompt_manager
    )
    
    # Assert
    assert analyzer.llm_service is llm_service_with_mocked_model
    assert analyzer.prompt_manager is mock_prompt_manager

def test_analyze_document_orchestration(llm_service_with_mocked_model, mock_prompt_manager):
    """
    Tests that analyze_document correctly orchestrates calls to its dependencies (prompt manager and llm service).
    """
    # Arrange
    analyzer = LLMComplianceAnalyzer(
        llm_service=llm_service_with_mocked_model,
        prompt_manager=mock_prompt_manager
    )
    
    # Act
    result = analyzer.analyze_document("Test document text", "Test context")

    # Assert
    # 1. Verify that the prompt was built
    mock_prompt_manager.build_prompt.assert_called_once_with(
        context="Test context",
        document_text="Test document text"
    )

    # 2. Verify that the llm_service was called with the generated prompt
    llm_service_with_mocked_model.generate_analysis.assert_called_once_with("This is a formatted prompt.")

    # 3. Verify the result is the parsed JSON from the mocked LLM
    assert "findings" in result
    assert result["findings"][0]["text"] == "Mocked LLM analysis."