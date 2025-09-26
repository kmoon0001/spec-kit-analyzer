import pytest
from unittest.mock import patch, MagicMock

from src.core.analysis_service import AnalysisService

@pytest.fixture
def mock_dependencies():
    """
    Mocks all the sub-services that AnalysisService initializes to test its orchestration logic
    without any real model loading, file I/O, or database access.
    """
    # We patch every external class that AnalysisService tries to initialize.
    with patch('src.core.analysis_service.LLMService') as mock_llm, \
         patch('src.core.analysis_service.FactCheckerService') as mock_fc, \
         patch('src.core.analysis_service.NERPipeline') as mock_ner, \
         patch('src.core.analysis_service.HybridRetriever') as mock_retriever, \
         patch('src.core.analysis_service.PreprocessingService') as mock_preproc, \
         patch('src.core.analysis_service.ReportGenerator') as mock_reporter, \
         patch('src.core.analysis_service.DocumentClassifier') as mock_classifier, \
         patch('src.core.analysis_service.NLGService') as mock_nlg, \
         patch('src.core.analysis_service.PromptManager') as mock_pm, \
         patch('src.core.analysis_service.ExplanationEngine') as mock_ee, \
         patch('src.core.analysis_service.ComplianceAnalyzer') as mock_analyzer, \
         patch('src.core.analysis_service.parse_document_content') as mock_parser, \
         patch('src.core.analysis_service.yaml.safe_load') as mock_yaml:

        # Configure a dummy config so that __init__ can run without errors
        mock_yaml.return_value = {
            'models': {
                'generator': 'dummy', 'generator_filename': 'dummy', 'fact_checker': 'dummy',
                'ner_ensemble': [], 'doc_classifier_prompt': '', 'nlg_prompt_template': '',
                'analysis_prompt_template': ''
            },
            'llm_settings': {}
        }

        # Configure the return values for the mocked components that are called
        mock_parser.return_value = [{'sentence': 'This is a test sentence.'}]
        # The instance of the classifier mock needs to have its method configured
        mock_classifier.return_value.classify_document.return_value = "Progress Note"
        # The instance of the analyzer mock is what gets called
        mock_analyzer.return_value.analyze_document.return_value = {"findings": ["test finding"]}

        # Yield a dictionary of the mock objects for assertions in the test
        yield {
            'parser': mock_parser,
            'preproc': mock_preproc,
            'classifier': mock_classifier,
            'analyzer': mock_analyzer
        }

def test_full_analysis_pipeline_orchestration(mock_dependencies):
    """
    Tests that AnalysisService.analyze_document correctly orchestrates its sub-components.
    """
    # Arrange: Initializing the service will use all the mocked components from the fixture
    service = AnalysisService()
    test_file_path = "/fake/path/to/doc.txt"

    # Act: Call the method being tested
    result = service.analyze_document(test_file_path, discipline="PT")

    # Assert
    # 1. Verify that the document was parsed and preprocessed
    mock_dependencies['parser'].assert_called_once_with(test_file_path)
    mock_dependencies['preproc'].return_value.correct_text.assert_called_once()

    # 2. Verify that the document was classified
    mock_dependencies['classifier'].return_value.classify_document.assert_called_once()

    # 3. Verify that the core analysis was performed with the correct arguments
    analyze_call_args = mock_dependencies['analyzer'].return_value.analyze_document.call_args
    assert analyze_call_args.kwargs['doc_type'] == "Progress Note"
    assert analyze_call_args.kwargs['discipline'] == "PT"

    # 4. Verify that the final result from the analyzer is returned
    assert result == {"findings": ["test finding"]}