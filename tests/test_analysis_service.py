import pytest
from unittest.mock import patch, MagicMock

from src.core.analysis_service import AnalysisService

@pytest.fixture
def mock_dependencies():
    """A fixture to mock all dependencies of the new AnalysisService architecture."""
    mock_config = MagicMock()
    mock_config.models.generator = "dummy_generator"
    mock_config.models.generator_filename = None
    mock_config.models.fact_checker = "dummy_fact_checker"
    mock_config.models.ner_ensemble = ["dummy_ner"]
    mock_config.models.doc_classifier_prompt = "dummy.txt"
    mock_config.models.analysis_prompt_template = "dummy.txt"
    mock_config.llm_settings = {}

    with patch('src.core.analysis_service.get_config', return_value=mock_config), \
         patch('src.core.analysis_service.LLMService'), \
         patch('src.core.analysis_service.FactCheckerService'), \
         patch('src.core.analysis_service.NERPipeline'), \
         patch('src.core.analysis_service.ReportGenerator'), \
         patch('src.core.analysis_service.ExplanationEngine'), \
         patch('src.core.analysis_service.DocumentClassifier') as mock_doc_classifier, \
         patch('src.core.analysis_service.PromptManager'), \
         patch('src.core.analysis_service.ComplianceAnalyzer') as mock_analyzer, \
         patch('src.core.analysis_service.parse_document_content') as mock_parse:
        
        # Setup mock return values
        mock_parse.return_value = [{'sentence': 'This is a test.'}]
        mock_doc_classifier.return_value.classify_document.return_value = "Test Note"
        mock_analyzer.return_value.analyze_document.return_value = {"findings": ["Test Finding"]}

        yield {
            'mock_parse': mock_parse,
            'mock_doc_classifier': mock_doc_classifier.return_value,
            'mock_analyzer': mock_analyzer.return_value
        }

def test_analysis_service_orchestration(mock_dependencies):
    """
    Tests that the new AnalysisService correctly orchestrates its dependencies.
    """
    # Arrange: The new AnalysisService requires a retriever instance at initialization.
    mock_retriever = MagicMock()
    
    # Act: Instantiate the service. Its __init__ will use the patched classes.
    service = AnalysisService(retriever=mock_retriever)
    result = service.analyze_document(file_path="fake/doc.txt", discipline="PT")

    # Assert: Verify that the orchestration logic calls the correct methods in sequence.
    mock_dependencies['mock_parse'].assert_called_once_with("fake/doc.txt")
    mock_dependencies['mock_doc_classifier'].classify_document.assert_called_once_with("This is a test.")
    mock_dependencies['mock_analyzer'].analyze_document.assert_called_once_with(
        document_text="This is a test.",
        discipline="PT",
        doc_type="Test Note"
    )

    # Assert the final result is passed through from the analyzer
    assert result == {"findings": ["Test Finding"]}
