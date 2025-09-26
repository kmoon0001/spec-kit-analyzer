import pytest
from unittest.mock import patch

# To test the full pipeline, we don't need to run the actual script.
# Instead, we can test the behavior of the main orchestrator, the AnalysisService.
# This test verifies that when analyze_document is called, all the correct sub-components
# are called in the right order.

from src.core.analysis_service import AnalysisService

@pytest.fixture
def mock_dependencies():
    """Mocks all the sub-services that AnalysisService initializes."""
    with patch('src.core.analysis_service.LLMService') as mock_llm, \
         patch('src.core.analysis_service.FactCheckerService') as mock_fact_checker, \
         patch('src.core.analysis_service.NERPipeline') as mock_ner, \
         patch('src.core.analysis_service.HybridRetriever') as mock_retriever, \
         patch('src.core.analysis_service.ReportGenerator') as mock_reporter, \
         patch('src.core.analysis_service.ExplanationEngine') as mock_explanation, \
         patch('src.core.analysis_service.DocumentClassifier') as mock_classifier, \
         patch('src.core.analysis_service.PromptManager') as mock_prompt_manager, \
         patch('src.core.analysis_service.ComplianceAnalyzer') as mock_analyzer, \
         patch('src.core.analysis_service.parse_document_content') as mock_parser, \
         patch('src.core.analysis_service.yaml.safe_load') as mock_yaml:
        
        # Configure return values for the mocked components
        mock_parser.return_value = [{'sentence': 'This is a test sentence.'}]
        mock_classifier.return_value.classify_document.return_value = "Progress Note"
        mock_analyzer.return_value.analyze_document.return_value = {"findings": ["finding1"]}

        yield {
            'parser': mock_parser,
            'classifier': mock_classifier,
            'analyzer': mock_analyzer,
        }

def test_full_analysis_pipeline_orchestration(mock_dependencies):
    """
    Tests that the AnalysisService correctly orchestrates the entire pipeline.
    """
    # Arrange
    # Initializing the service will use all the mocked components from the fixture
    service = AnalysisService()
    test_file_path = "/fake/path/to/doc.txt"

    # Act
    result = service.analyze_document(test_file_path, "PT")

    # Assert
    # 1. Verify that the document was parsed
    mock_dependencies['parser'].assert_called_once_with(test_file_path)

    # 2. Verify that the document was classified
    mock_dependencies['classifier'].return_value.classify_document.assert_called_once()

    # 3. Verify that the core analysis was performed with the classified doc_type
    analyze_call_args = mock_dependencies['analyzer'].return_value.analyze_document.call_args
    assert analyze_call_args.kwargs['doc_type'] == "Progress Note"

    # 4. Verify the final output is the result from the analyzer
    assert result == {"findings": ["finding1"]}
