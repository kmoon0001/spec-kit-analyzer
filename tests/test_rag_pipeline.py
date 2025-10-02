import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from src.core.analysis_service import AnalysisService
from src.core.hybrid_retriever import HybridRetriever


@pytest.fixture
def mock_dependencies():
    """
    Mocks all the sub-services that AnalysisService initializes to test its orchestration logic
    without any real model loading, file I/O, or database access.
    """
    with patch("src.core.analysis_service.LLMService"), \
         patch("src.core.analysis_service.HybridRetriever") as mock_retriever_cls, \
         patch("src.core.analysis_service.ReportGenerator") as mock_reporter_cls, \
         patch("src.core.analysis_service.DocumentClassifier") as mock_classifier_cls, \
         patch("src.core.analysis_service.parse_document_content") as mock_parser, \
         patch("src.core.analysis_service.yaml.safe_load") as mock_yaml, \
         patch("src.core.analysis_service.ComplianceAnalyzer") as mock_analyzer_cls, \
         patch("src.core.analysis_service.PreprocessingService"), \
         patch("src.core.analysis_service.PhiScrubberService"), \
         patch("src.core.analysis_service.ExplanationEngine"), \
         patch("src.core.analysis_service.FactCheckerService"), \
         patch("src.core.analysis_service.NLGService"), \
         patch("src.core.analysis_service.PromptManager"), \
         patch("src.core.analysis_service.ChecklistService"):

        # Mock config loading
        mock_yaml.return_value = {
            "models": {
                "generator": "dummy", "generator_filename": "dummy", "fact_checker": "dummy",
                "ner_ensemble": [], "doc_classifier_prompt": "dummy.txt",
                "nlg_prompt_template": "dummy.txt", "analysis_prompt_template": "dummy.txt"
            },
            "llm_settings": {}, "retrieval": {}, "analysis": {},
        }

        # Mock file parsing
        mock_parser.return_value = [{"sentence": "This is a test sentence."}]

        # Mock service behaviors
        mock_classifier_cls.return_value.classify_document = AsyncMock(return_value="Progress Note")
        mock_retriever_cls.return_value.retrieve = AsyncMock(return_value=[])

        mock_analysis_result = {"findings": [{"issue_title": "test finding"}]}
        mock_analyzer_cls.return_value.analyze_document = AsyncMock(return_value=mock_analysis_result)

        mock_reporter_cls.return_value.generate_report = AsyncMock(
            return_value={"summary": "Report Summary", "analysis": mock_analysis_result}
        )

        yield {
            "parser": mock_parser,
            "classifier": mock_classifier_cls.return_value,
            "analyzer": mock_analyzer_cls.return_value,
            "reporter": mock_reporter_cls.return_value,
        }


@pytest.mark.asyncio
async def test_full_analysis_pipeline_orchestration(mock_dependencies):
    """
    Tests that AnalysisService.analyze_document correctly orchestrates its sub-components.
    """
    # test code here

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

# Assert – Verify the initial calls and pipeline orchestration
mock_dependencies["parser"].assert_called_once_with(test_file_path)
mock_dependencies["classifier"].classify_document.assert_awaited_once()

# Verify that the core analysis was delegated correctly
analyze_call_args = mock_dependencies["analyzer"].analyze_document.call_args
assert "document_text" in analyze_call_args.kwargs
assert analyze_call_args.kwargs["discipline"] == "PT"
assert analyze_call_args.kwargs["doc_type"] == "Progress Note"

# Verify final report is generated and returned
mock_dependencies["reporter"].generate_report.assert_awaited_once()

# Final result checks
assert "summary" in result
assert result["analysis"]["findings"] == [{"issue_title": "test finding"}]