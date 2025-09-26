import pytest
from unittest.mock import patch, MagicMock
import os

# We need to import the class to be tested
from src.core.analysis_service import AnalysisService

@pytest.fixture
def mock_all_sub_services():
    """A fixture to mock all dependencies of AnalysisService for isolated testing."""

    # Define a mock config object that mimics the structure of AppConfig
    mock_config = MagicMock()
    mock_config.models.generator = "dummy_generator"
    mock_config.models.generator_filename = "dummy_generator.gguf"
    mock_config.models.fact_checker = "dummy_fact_checker"
    mock_config.models.ner_ensemble = ["dummy_ner_model"]
    mock_config.models.doc_classifier_prompt = "dummy_doc_prompt.txt"
    mock_config.models.nlg_prompt_template = "dummy_nlg_template.txt"
    mock_config.models.analysis_prompt_template = "dummy_analysis_template.txt"
    mock_config.llm_settings = {}

    with patch('src.core.analysis_service.get_config', return_value=mock_config) as mock_get_config, \
         patch('src.core.analysis_service.LLMService') as mock_LLMService, \
         patch('src.core.analysis_service.FactCheckerService') as mock_FactCheckerService, \
         patch('src.core.analysis_service.NERPipeline') as mock_NERPipeline, \
         patch('src.core.analysis_service.HybridRetriever') as mock_HybridRetriever, \
         patch('src.core.analysis_service.PreprocessingService') as mock_PreprocessingService, \
         patch('src.core.analysis_service.ReportGenerator') as mock_ReportGenerator, \
         patch('src.core.analysis_service.ExplanationEngine') as mock_ExplanationEngine, \
         patch('src.core.analysis_service.DocumentClassifier') as mock_DocumentClassifier, \
         patch('src.core.analysis_service.NLGService') as mock_NLGService, \
         patch('src.core.analysis_service.PromptManager') as mock_PromptManager, \
         patch('src.core.analysis_service.LLMComplianceAnalyzer') as mock_LLMComplianceAnalyzer, \
         patch('src.core.analysis_service.parse_document_content') as mock_parse_document_content:

        # This dictionary will hold the instances of the mocks, not the classes
        mocks = {
            'get_config': mock_get_config,
            'LLMService': mock_LLMService.return_value,
            'FactCheckerService': mock_FactCheckerService.return_value,
            'NERPipeline': mock_NERPipeline.return_value,
            'HybridRetriever': mock_HybridRetriever.return_value,
            'PreprocessingService': mock_PreprocessingService.return_value,
            'ReportGenerator': mock_ReportGenerator.return_value,
            'ExplanationEngine': mock_ExplanationEngine.return_value,
            'DocumentClassifier': mock_DocumentClassifier.return_value,
            'NLGService': mock_NLGService.return_value,
            'PromptManager': mock_PromptManager.return_value,
            'LLMComplianceAnalyzer': mock_LLMComplianceAnalyzer.return_value,
            'parse_document_content': mock_parse_document_content
        }
        yield mocks

def test_analysis_service_orchestration(mock_all_sub_services):
    """
    Tests that AnalysisService.analyze_document correctly orchestrates its sub-components.
    """
    # Arrange: Configure the return values of the mocked dependencies
    mock_all_sub_services['parse_document_content'].return_value = [{'sentence': 'This is a test.'}]
    mock_all_sub_services['PreprocessingService'].correct_text.return_value = "This is a corrected test."
    mock_all_sub_services['DocumentClassifier'].classify_document.return_value = "Test Note"
    mock_all_sub_services['HybridRetriever'].retrieve.return_value = [] # empty rules
    mock_all_sub_services['LLMComplianceAnalyzer'].analyze_document.return_value = {"findings": ["finding1"]}
    mock_all_sub_services['ExplanationEngine'].add_explanations.return_value = {"findings": [{"confidence": 0.9, "rule_id": "123"}]}
    mock_all_sub_services['FactCheckerService'].is_finding_plausible.return_value = True
    mock_all_sub_services['NLGService'].generate_personalized_tip.return_value = "A helpful tip."

    # Act: Instantiate the service. Its __init__ method will now use all the mocks.
    service = AnalysisService()
    result = service.analyze_document(file_path="fake/doc.txt", discipline="PT")

    # Assert: Verify that the orchestration logic calls the correct methods
    mock_all_sub_services['parse_document_content'].assert_called_once_with("fake/doc.txt")
    mock_all_sub_services['PreprocessingService'].correct_text.assert_called_once_with("This is a test.")
    mock_all_sub_services['DocumentClassifier'].classify_document.assert_called_once_with("This is a corrected test.")
    mock_all_sub_services['HybridRetriever'].retrieve.assert_called_once()
    mock_all_sub_services['LLMComplianceAnalyzer'].analyze_document.assert_called_once()
    mock_all_sub_services['ExplanationEngine'].add_explanations.assert_called_once()
    mock_all_sub_services['NLGService'].generate_personalized_tip.assert_called_once()

    # Check final result structure
    assert "findings" in result
    assert "personalized_tip" in result["findings"][0]