import pytest
from unittest.mock import MagicMock, patch
from src.compliance_analyzer import ComplianceAnalyzer

@pytest.fixture
def mock_config():
    """Fixture for mock config"""
    return {
        "models": {
            "ner_model": "dslim/bert-base-NER",
            "prompt_template": "default_prompt.txt",
            "quantization": "none"
        }
    }

@pytest.fixture
def mock_guideline_service():
    """Fixture for mock GuidelineService"""
    return MagicMock()

@pytest.fixture
def mock_retriever():
    """Fixture for mock HybridRetriever"""
    retriever = MagicMock()
    retriever.retrieve.return_value = [
        {"issue_title": "Test Rule", "issue_detail": "Details", "suggestion": "Suggestion"}
    ]
    return retriever

@patch('src.compliance_analyzer.NERPipeline')
@patch('src.compliance_analyzer.PromptManager')
@patch('src.compliance_analyzer.ExplanationEngine')
def test_compliance_analyzer_initialization(mock_explanation_engine, mock_prompt_manager, mock_ner_pipeline, mock_config, mock_guideline_service, mock_retriever):
    """Tests the initialization of the ComplianceAnalyzer"""
    analyzer = ComplianceAnalyzer(mock_config, mock_guideline_service, mock_retriever)
    mock_ner_pipeline.assert_called_once_with(model_name=mock_config['models']['ner_model'])
    mock_prompt_manager.assert_called_once_with(template_path=mock_config['models']['prompt_template'])
    assert isinstance(analyzer.explanation_engine, MagicMock)

@patch('src.compliance_analyzer.NERPipeline')
@patch('src.compliance_analyzer.PromptManager')
@patch('src.compliance_analyzer.ExplanationEngine')
def test_analyze_document(mock_explanation_engine, mock_prompt_manager, mock_ner_pipeline, mock_config, mock_guideline_service, mock_retriever):
    """Tests the document analysis workflow"""
    # Setup mocks
    mock_ner_pipeline.return_value.extract_entities.return_value = [{"entity_group": "Test", "word": "Entity"}]
    mock_prompt_manager.return_value.build_prompt.return_value = "Test prompt"
    mock_explanation_engine.return_value.add_explanations.return_value = {"explained": True}

    analyzer = ComplianceAnalyzer(mock_config, mock_guideline_service, mock_retriever)
    analyzer.ner_pipeline = mock_ner_pipeline.return_value
    analyzer.prompt_manager = mock_prompt_manager.return_value
    analyzer.explanation_engine = mock_explanation_engine.return_value

    result = analyzer.analyze_document("Test document", "PT", "evaluation")

    # Assertions
    mock_ner_pipeline.return_value.extract_entities.assert_called_once_with("Test document")
    mock_retriever.retrieve.assert_called_once()
    mock_prompt_manager.return_value.build_prompt.assert_called_once()
    mock_explanation_engine.return_value.add_explanations.assert_called_once()
    assert result == {"explained": True}