import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from types import SimpleNamespace

from src.core.analysis_service import AnalysisService
from src.config import Settings, LLMSettings, PathsSettings, DatabaseSettings, AuthSettings, RetrievalSettings, AnalysisSettings, MaintenanceSettings


@pytest.fixture
def mock_settings() -> Settings:
    """Provides a fully-structured mock Settings object for testing."""
    return Settings(
        api_url="http://test.com",
        use_ai_mocks=True,
        database=DatabaseSettings(url="sqlite+aiosqlite:///./test.db", echo=False),
        auth=AuthSettings(
            secret_key="test_secret",
            algorithm="HS256",
            access_token_expire_minutes=30,
        ),
        paths=PathsSettings(
            temp_upload_dir="tmp/uploads",
            rule_dir="src/resources/rules",
            medical_dictionary="src/resources/medical_dictionary.txt",
            analysis_prompt_template="src/resources/prompts/analysis_prompt_template.txt",
            nlg_prompt_template="src/resources/prompts/nlg_prompt_template.txt",
            doc_classifier_prompt="src/resources/prompts/doc_classifier_prompt.txt",
        ),
        llm=LLMSettings(
            repo="test-repo",
            filename="test-model.gguf",
            model_type="test-type",
            context_length=1024,
            generation_params={"max_new_tokens": 100},
        ),
        retrieval=RetrievalSettings(
            dense_model_name="test-retriever",
            similarity_top_k=3,
            rrf_k=50,
        ),
        analysis=AnalysisSettings(
            confidence_threshold=0.6,
            deterministic_focus="Test focus",
        ),
        maintenance=MaintenanceSettings(
            purge_retention_days=30,
            purge_interval_days=1,
        ),
    )


@pytest.mark.asyncio
@patch("src.core.analysis_service.parse_document_content")
@patch("src.core.analysis_service.ComplianceAnalyzer")
@patch("src.core.analysis_service.DocumentClassifier")
@patch("src.core.analysis_service.PreprocessingService")
async def test_analysis_service_orchestration(
    mock_preproc_cls,
    mock_doc_classifier_cls,
    mock_analyzer_cls,
    mock_parse_content,
    mock_settings,
):
    """
    Tests that AnalysisService correctly orchestrates its dependencies
    using the new centralized configuration system.
    """
    # Arrange: Mock the return values of the service dependencies
    mock_parse_content.return_value = [{"sentence": "This is a test document."}]

    mock_preproc_instance = mock_preproc_cls.return_value
    mock_preproc_instance.correct_text = AsyncMock(return_value="This is a corrected document.")

    mock_doc_classifier_instance = mock_doc_classifier_cls.return_value
    mock_doc_classifier_instance.classify_document = AsyncMock(return_value="Progress Note")

    mock_analyzer_instance = mock_analyzer_cls.return_value
    mock_analyzer_instance.analyze_document = AsyncMock(
        return_value={"findings": [{"rule_id": "TEST-01"}]}
    )

    # Patch get_settings to return our mock settings object
    with patch("src.core.analysis_service.get_settings", return_value=mock_settings):
        # Act: Instantiate the service. Its __init__ will now use the mocked settings.
        service = AnalysisService(retriever=MagicMock())

        # Mock open to avoid FileNotFoundError when the service tries to read the document
        with patch("builtins.open", MagicMock()):
            result = await service.analyze_document(
                file_path="fake/doc.txt", discipline="PT", analysis_mode="rubric"
            )

    # Assert: Verify the orchestration logic
    mock_parse_content.assert_called_once_with("fake/doc.txt")
    mock_preproc_instance.correct_text.assert_awaited_once_with("This is a test document.")
    mock_doc_classifier_instance.classify_document.assert_awaited_once_with("This is a corrected document.")
    mock_analyzer_instance.analyze_document.assert_awaited_once_with(
        document_text="This is a corrected document.",
        discipline="PT",
        doc_type="Progress Note",
    )

    assert "analysis" in result
    assert result["analysis"]["findings"][0]["rule_id"] == "TEST-01"