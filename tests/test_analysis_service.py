import pytest
from unittest.mock import patch, MagicMock
import asyncio

# Ensure the src directory is in the Python path
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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
    mock_config.llm_settings.dict.return_value = {}

    with (
        patch("src.core.analysis_service.get_settings", return_value=mock_config),
        patch("src.core.analysis_service.LLMService"),
        patch("src.core.analysis_service.FactCheckerService"),
        patch("src.core.analysis_service.NERPipeline"),
        patch("src.core.analysis_service.ReportGenerator"),
        patch("src.core.analysis_service.ExplanationEngine"),
        patch("src.core.analysis_service.DocumentClassifier") as mock_doc_classifier,
        patch("src.core.analysis_service.PromptManager"),
        patch("src.core.analysis_service.ComplianceAnalyzer") as mock_analyzer,
        patch("src.core.analysis_service.parse_document_content") as mock_parse,
        patch("src.core.analysis_service.PreprocessingService") as mock_preproc,
    ):
        # Setup mock return values
        mock_parse.return_value = [{"sentence": "This is a test."}]

        # Mock preprocessing to return the text as-is
        correct_text_future = asyncio.Future()
        correct_text_future.set_result("This is a test.")
        mock_preproc.return_value.correct_text.return_value = correct_text_future

        # Use asyncio.Future for async mock return values
        classify_future = asyncio.Future()
        classify_future.set_result("Test Note")
        mock_doc_classifier.return_value.classify_document.return_value = (
            classify_future
        )

        analyze_future = asyncio.Future()
        analyze_future.set_result({"findings": [{"issue_title": "Test Finding"}]})
        mock_analyzer.return_value.analyze_document.return_value = analyze_future

        yield {
            "mock_parse": mock_parse,
            "mock_doc_classifier": mock_doc_classifier.return_value,
            "mock_analyzer": mock_analyzer.return_value,
            "mock_preproc": mock_preproc.return_value,
        }


@pytest.mark.asyncio
async def test_analysis_service_orchestration(mock_dependencies):
    """Tests that the new AnalysisService correctly orchestrates its dependencies."""
    # Arrange: The new AnalysisService requires a retriever instance at initialization.
    mock_retriever = MagicMock()

    # Act: Instantiate the service. Its __init__ will use the patched classes.
    service = AnalysisService(retriever=mock_retriever)

    # Mock the open call to avoid FileNotFoundError
    with patch("builtins.open", MagicMock()):
        result = await service.analyze_document(
            file_path="fake/doc.txt", discipline="PT"
        )

    # Assert: Verify that the orchestration logic calls the correct methods in sequence.
    mock_dependencies["mock_parse"].assert_called_once()
    mock_dependencies["mock_preproc"].correct_text.assert_called_once_with(
        "This is a test."
    )
    mock_dependencies["mock_doc_classifier"].classify_document.assert_called_once_with(
        "This is a test."
    )
    mock_dependencies["mock_analyzer"].analyze_document.assert_called_once_with(
        document_text="This is a test.", discipline="PT", doc_type="Test Note"
    )

    # Assert the final result contains the enriched analysis data
    assert "analysis" in result
    assert result["analysis"]["findings"] == [{"issue_title": "Test Finding"}]
