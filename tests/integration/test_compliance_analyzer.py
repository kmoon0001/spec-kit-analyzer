from unittest.mock import MagicMock

import pytest

# Import the class we are testing
from src.core.llm_analyzer import LLMComplianceAnalyzer
from src.core.llm_service import LLMService
from src.utils.prompt_manager import PromptManager

# --- Mocks and Fixtures ---


@pytest.fixture
def mock_prompt_manager():
    """A mock for the PromptManager."""
    pm = MagicMock(spec=PromptManager)
    pm.get_prompt.return_value = "This is a formatted prompt."
    return pm


@pytest.fixture
def mock_llm_service():
    """
    Mocks the LLMService to prevent model downloads and control its behavior.
    This is a more robust way to mock the service for these specific tests.
    """
    # We create a mock instance of the service, specifying the class to ensure
    # that the mock has the same methods and properties as the real service.
    service = MagicMock(spec=LLMService)
    # We configure the return value of the method that is called by the analyzer.
    service.generate.return_value = '{"findings": [{"text": "Mocked LLM analysis."}]}'
    yield service


# --- Tests ---


def test_llm_compliance_analyzer_initialization(mock_llm_service, mock_prompt_manager):
    """
    Tests that the LLMComplianceAnalyzer correctly initializes with its dependencies.
    """
    # Act
    analyzer = LLMComplianceAnalyzer(llm_service=mock_llm_service, prompt_manager=mock_prompt_manager)

    # Assert
    assert analyzer.llm_service is mock_llm_service
    assert analyzer.prompt_manager is mock_prompt_manager


def test_analyze_document_orchestration(mock_llm_service, mock_prompt_manager):
    """Tests that analyze_document correctly orchestrates calls to its dependencies."""
    # Arrange
    analyzer = LLMComplianceAnalyzer(llm_service=mock_llm_service, prompt_manager=mock_prompt_manager)

    # Act
    result = analyzer.analyze_document("Test document text", "Test context")

    # Assert
    # 1. Verify that the prompt was built
    mock_prompt_manager.get_prompt.assert_called_once_with(context="Test context", document_text="Test document text")

    # 2. Verify that the llm_service was called with the generated prompt
    mock_llm_service.generate.assert_called_once_with("This is a formatted prompt.")

    # 3. Verify the result is the parsed JSON from the mocked LLM
    assert "findings" in result
    assert result["findings"][0]["text"] == "Mocked LLM analysis."
