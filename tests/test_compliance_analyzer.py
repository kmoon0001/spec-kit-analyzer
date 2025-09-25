import pytest
from unittest.mock import MagicMock, patch

# Import the class we are testing
from src.core.compliance_analyzer import ComplianceAnalyzer

# --- Mocks for all dependencies ---

@pytest.fixture
def mock_retriever():
    retriever = MagicMock()
    retriever.retrieve.return_value = [{"issue_title": "Mocked Rule"}]
    return retriever

@pytest.fixture
def mock_ner_pipeline():
    ner = MagicMock()
    ner.extract_entities.return_value = [{"entity_group": "Test", "word": "Entity"}]
    return ner

@pytest.fixture
def mock_llm_service():
    llm = MagicMock()
    llm.generate_analysis.return_value = '{"findings": [{"text": "Problematic text."}]}'
    return llm

@pytest.fixture
def mock_nlg_service():
    nlg = MagicMock()
    nlg.generate_personalized_tip.return_value = "This is a generated tip."
    return nlg

@pytest.fixture
def mock_explanation_engine():
    exp = MagicMock()
    exp.add_explanations.return_value = {"findings": [{"text": "Problematic text."}]}
    return exp

@pytest.fixture
def mock_prompt_manager():
    pm = MagicMock()
    pm.build_prompt.return_value = "This is a test prompt."
    return pm

# --- Tests ---

def test_compliance_analyzer_initialization(
    mock_retriever, mock_ner_pipeline, mock_llm_service, 
    mock_nlg_service, mock_explanation_engine, mock_prompt_manager
):
    """Tests that the ComplianceAnalyzer correctly initializes with all its dependencies."""
    # Act
    analyzer = ComplianceAnalyzer(
        retriever=mock_retriever,
        ner_pipeline=mock_ner_pipeline,
        llm_service=mock_llm_service,
        nlg_service=mock_nlg_service,
        explanation_engine=mock_explanation_engine,
        prompt_manager=mock_prompt_manager
    )
    
    # Assert
    assert analyzer.retriever is mock_retriever
    assert analyzer.ner_pipeline is mock_ner_pipeline
    assert analyzer.llm_service is mock_llm_service
    assert analyzer.nlg_service is mock_nlg_service


def test_analyze_document_orchestration(
    mock_retriever, mock_ner_pipeline, mock_llm_service, 
    mock_nlg_service, mock_explanation_engine, mock_prompt_manager
):
    """
    Tests that analyze_document correctly orchestrates calls to its dependencies.
    """
    # Arrange
    analyzer = ComplianceAnalyzer(
        retriever=mock_retriever,
        ner_pipeline=mock_ner_pipeline,
        llm_service=mock_llm_service,
        nlg_service=mock_nlg_service,
        explanation_engine=mock_explanation_engine,
        prompt_manager=mock_prompt_manager
    )
    
    # Act
    result = analyzer.analyze_document("Test document", "PT", "evaluation")

    # Assert
    # 1. Verify the orchestration flow
    mock_ner_pipeline.extract_entities.assert_called_once_with("Test document")
    mock_retriever.retrieve.assert_called_once()
    mock_prompt_manager.build_prompt.assert_called_once()
    mock_llm_service.generate_analysis.assert_called_once()
    mock_explanation_engine.add_explanations.assert_called_once()
    mock_nlg_service.generate_personalized_tip.assert_called_once()

    # 2. Verify the final result includes the generated tip
    assert "findings" in result
    assert result["findings"][0]["personalized_tip"] == "This is a generated tip."
