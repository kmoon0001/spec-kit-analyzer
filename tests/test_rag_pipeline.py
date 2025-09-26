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
    with patch("src.core.analysis_service.HybridRetriever") as mock_retriever, patch(
        "src.core.analysis_service.PreprocessingService"
    ) as mock_preproc, patch(
        "src.core.analysis_service.DocumentClassifier"
    ) as mock_classifier, patch(
        "src.core.analysis_service.ComplianceAnalyzer"
    ) as mock_analyzer, patch(
        "src.core.analysis_service.ReportGenerator"
    ) as mock_reporter, patch(
        "src.core.analysis_service.parse_document_content"
    ) as mock_parser, patch(
        "src.core.analysis_service.yaml.safe_load"
    ) as mock_yaml:  # Mock config loading

        # Configure return values for the mocked components
        mock_parser.return_value = [{"sentence": "This is a test sentence."}]
        mock_classifier.return_value.classify_document.return_value = "Progress Note"
        mock_analyzer.return_value.analyze_document.return_value = {"findings": []}
        mock_reporter.return_value.generate_html_report.return_value = (
            "<html>Mock Report</html>"
        )

        yield {
            "retriever": mock_retriever,
            "preproc": mock_preproc,
            "classifier": mock_classifier,
            "analyzer": mock_analyzer,
            "reporter": mock_reporter,
            "parser": mock_parser,
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
    report = service.analyze_document(
        test_file_path, discipline="PT", analysis_mode="rubric"
    )

    # Assert
    # 1. Verify that the document was parsed and preprocessed
    mock_dependencies["parser"].assert_called_once_with(test_file_path)
    mock_dependencies["preproc"].return_value.correct_text.assert_called_once()

    # 2. Verify that the document was classified
    mock_dependencies["classifier"].return_value.classify_document.assert_called_once()

    # 3. Verify that the core analysis was performed with the classified doc_type
    analyze_call_args = mock_dependencies[
        "analyzer"
    ].return_value.analyze_document.call_args
    assert analyze_call_args.kwargs["doc_type"] == "Progress Note"

    # 4. Verify that the report was generated with the analysis result
    mock_dependencies["reporter"].return_value.generate_html_report.assert_called_once()

    # 5. Verify the final output
    assert report == "<html>Mock Report</html>"
