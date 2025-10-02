import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from src.core.analysis_service import AnalysisService
from src.core.hybrid_retriever import HybridRetriever


@pytest.fixture
def mock_all_dependencies():
    """Mocks all sub-services to test the orchestration logic of AnalysisService."""
    with patch(
        "src.core.analysis_service.parse_document_content"
    ) as mock_parse, patch(
        "src.core.analysis_service.PreprocessingService"
    ) as mock_preproc, patch(
        "src.core.analysis_service.DocumentClassifier"
    ) as mock_classifier, patch(
        "src.core.analysis_service.ComplianceAnalyzer"
    ) as mock_analyzer, patch(
        "src.core.analysis_service.ReportGenerator"
    ) as mock_reporter, patch(
        "src.core.analysis_service.ChecklistService"
    ) as mock_checklist:

        # Configure mock return values
        mock_parse.return_value = [{"sentence": "This is a test sentence."}]
        mock_preproc.return_value.correct_text = AsyncMock(
            return_value="This is a test sentence."
        )
        mock_classifier.return_value.classify_document = AsyncMock(
            return_value="Progress Note"
        )

        mock_analysis_result = {"findings": [{"issue_title": "test finding"}]}
        mock_analyzer.return_value.analyze_document = AsyncMock(
            return_value=mock_analysis_result
        )

        mock_checklist.return_value.evaluate.return_value = []

        mock_reporter.return_value.generate_report = AsyncMock(
            return_value={
                "summary": "Report Summary",
                "analysis": mock_analysis_result,
            }
        )

        yield {
            "parse": mock_parse,
            "preproc": mock_preproc.return_value,
            "classifier": mock_classifier.return_value,
            "analyzer": mock_analyzer.return_value,
            "reporter": mock_reporter.return_value,
            "checklist": mock_checklist.return_value,
        }


@pytest.mark.asyncio
async def test_full_analysis_pipeline_orchestration(mock_all_dependencies):
    """
    Tests that AnalysisService.analyze_document correctly orchestrates its sub-components.
    """
    # Arrange
    mock_retriever = MagicMock(spec=HybridRetriever)

    # We need to patch get_settings because it's called inside the __init__
    with patch("src.core.analysis_service.get_settings") as mock_get_settings:
        # Provide a mock settings object that has the necessary attributes
        mock_settings = MagicMock()
        mock_settings.models.analysis_prompt_template = "dummy.txt"
        mock_settings.models.nlg_prompt_template = "dummy.txt"
        mock_settings.models.doc_classifier_prompt = "dummy.txt"
        mock_settings.analysis.deterministic_focus = "focus"
        # Mock the model dump for LLMService initialization
        mock_settings.models.model_dump.return_value = {
            "generator_profiles": {
                "standard": {"repo": "test-repo", "filename": "test.gguf"}
            }
        }
        mock_settings.llm.model_dump.return_value = {}
        mock_get_settings.return_value = mock_settings

        service = AnalysisService(retriever=mock_retriever)

    test_file_path = "/fake/path/to/doc.txt"

    # Act
    result = await service.analyze_document(test_file_path, discipline="PT")

    # Assert
    mock_all_dependencies["parse"].assert_called_once_with(test_file_path)
    mock_all_dependencies["preproc"].correct_text.assert_awaited_once()
    mock_all_dependencies["classifier"].classify_document.assert_awaited_once()
    mock_all_dependencies["analyzer"].analyze_document.assert_awaited_once()
    mock_all_dependencies["checklist"].evaluate.assert_called_once()
    mock_all_dependencies["reporter"].generate_report.assert_awaited_once()

    assert "summary" in result
    assert result["analysis"]["findings"] == [{"issue_title": "test finding"}]