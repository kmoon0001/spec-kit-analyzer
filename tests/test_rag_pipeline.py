import pytest
from unittest.mock import patch, MagicMock

from src.core.analysis_service import AnalysisService

@pytest.fixture
def mock_dependencies():
    """
    Mocks all the sub-services that AnalysisService initializes to test its orchestration logic
    without any real model loading, file I/O, or database access.
    """
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

        mock_yaml.return_value = {
            'models': {
                'generator': 'dummy', 'generator_filename': 'dummy', 'fact_checker': 'dummy',
                'ner_ensemble': [], 'doc_classifier_prompt': '', 'nlg_prompt_template': '',
                'analysis_prompt_template': ''
            },
            'llm_settings': {}
        }

        mock_parser.return_value = [{'sentence': 'This is a test sentence.'}]
        mock_classifier.return_value.classify_document.return_value = "Progress Note"

        # This is the direct output from the ComplianceAnalyzer
        mock_analysis_result = {"findings": ["test finding"]}
        mock_analyzer.return_value.analyze_document.return_value = mock_analysis_result

        # The ReportGenerator will wrap this analysis result
        mock_reporter.return_value.generate_report.return_value = {
            "summary": "Report Summary",
            "analysis": mock_analysis_result
        }

        yield {
            'parser': mock_parser,
            'preproc': mock_preproc,
            'classifier': mock_classifier,
            'analyzer': mock_analyzer,
            'reporter': mock_reporter
        }

def test_full_analysis_pipeline_orchestration(mock_dependencies):
    """
    Tests that AnalysisService.analyze_document correctly orchestrates its sub-components.
    """
    service = AnalysisService()
    test_file_path = "/fake/path/to/doc.txt"

    result = service.analyze_document(test_file_path, discipline="PT")

    # Verify the initial steps
    mock_dependencies['parser'].assert_called_once_with(test_file_path)
    mock_dependencies['preproc'].return_value.correct_text.assert_called_once()
    mock_dependencies['classifier'].return_value.classify_document.assert_called_once()

    # Verify that the core analysis was delegated correctly
    analyze_call_args = mock_dependencies['analyzer'].return_value.analyze_document.call_args
    assert "document_text" in analyze_call_args.kwargs
    assert analyze_call_args.kwargs['discipline'] == "PT"
    assert analyze_call_args.kwargs['doc_type'] == "Progress Note"

    # Verify that the final report is generated and returned
    mock_dependencies['reporter'].return_value.generate_report.assert_called_once()
    assert "summary" in result
    assert result['analysis'] == {"findings": ["test finding"]}