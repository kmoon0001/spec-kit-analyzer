import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from src.core.analysis_service import AnalysisService
from src.config import (
    Settings,
    ModelsSettings,
    LLMSettings,
    PathsSettings,
    DatabaseSettings,
    AuthSettings,
    RetrievalSettings,
    AnalysisSettings,
    MaintenanceSettings,
)


@pytest.fixture
def dummy_document(tmp_path: Path) -> Path:
    """Creates a dummy document file for testing."""
    doc_path = tmp_path / "test_document.txt"
    doc_path.write_text("The patient shows improvement.", encoding="utf-8")
    return doc_path


@pytest.fixture
def mock_settings(tmp_path: Path) -> Settings:
    """Provides a fully-structured mock Settings object for integration testing."""
    # Create dummy directories and files that the service might need to access
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    analysis_prompt_path = prompts_dir / "analysis.txt"
    nlg_prompt_path = prompts_dir / "nlg.txt"
    doc_classifier_prompt_path = prompts_dir / "doc_classifier.txt"
    analysis_prompt_path.touch()
    nlg_prompt_path.touch()
    doc_classifier_prompt_path.touch()
@pytest.fixture
def mock_settings(tmp_path: Path) -> Settings:
    """Provides a fully-structured mock Settings object for integration testing."""
    # Create dummy prompt files
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    analysis_prompt_path = prompts_dir / "analysis.txt"
    nlg_prompt_path = prompts_dir / "nlg.txt"
    doc_classifier_prompt_path = prompts_dir / "doc_classifier.txt"
    analysis_prompt_path.touch()
    nlg_prompt_path.touch()
    doc_classifier_prompt_path.touch()

    # Explicitly create uploads and rules directories
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    from src.config import ModelsSettings

    return Settings(
        use_ai_mocks=True,
        enable_director_dashboard=True,
        database=DatabaseSettings(url="sqlite+aiosqlite:///./test.db", echo=False),
        auth=AuthSettings(
            secret_key="test_secret",
            algorithm="HS256",
            access_token_expire_minutes=30,
        ),
        paths=PathsSettings(
            temp_upload_dir=str(uploads_dir),
            rule_dir=str(rules_dir),
            api_url="http://test.com",
        ),
        models=ModelsSettings(
            retriever="test-retriever",
            fact_checker="test-fact-checker",
            ner_ensemble=["test-ner"],
            doc_classifier_prompt=str(doc_classifier_prompt_path),
            analysis_prompt_template=str(analysis_prompt_path),
            nlg_prompt_template=str(nlg_prompt_path),
            generator_profiles={
                "standard": {
                    "repo": "test-repo",
                    "filename": "test.gguf",
                }
            },
        ),
        llm=LLMSettings(
            model_type="llama",
            context_length=4096,
            generation_params={"temperature": 0.1},
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

            generation_params={"temperature": 0.1},
        ),
        retrieval=RetrievalSettings(
            dense_model_name="test-retriever", similarity_top_k=3, rrf_k=50
        ),
        analysis=AnalysisSettings(
            confidence_threshold=0.6, deterministic_focus="Test focus"
        ),
        maintenance=MaintenanceSettings(purge_retention_days=30, purge_interval_days=1),
        models=ModelsSettings(
            retriever="test-retriever",
            fact_checker="test-fact-checker",
            ner_ensemble=[],
            doc_classifier_prompt=str(doc_classifier_prompt_path),
            analysis_prompt_template=str(analysis_prompt_path),
            nlg_prompt_template=str(nlg_prompt_path),
        ),
    )


@pytest.mark.asyncio
@patch("src.core.analysis_service.parse_document_content")
@patch("src.core.analysis_service.ComplianceAnalyzer")
@patch("src.core.analysis_service.DocumentClassifier")
@patch("src.core.analysis_service.PreprocessingService")
async def test_full_analysis_pipeline(
    mock_preproc_cls,
    mock_doc_classifier_cls,
    mock_analyzer_cls,
    mock_parse_content,
    mock_settings: Settings,
    dummy_document: Path,
):
    """
    Ensures AnalysisService orchestrates its dependencies correctly using a
    properly mocked configuration.
    """
    # Arrange
    mock_parse_content.return_value = [{"sentence": "The patient shows improvement."}]

    mock_preproc_instance = mock_preproc_cls.return_value
    mock_preproc_instance.correct_text = AsyncMock(
        return_value="The patient shows improvement."
    )

    mock_doc_classifier_instance = mock_doc_classifier_cls.return_value
    mock_doc_classifier_instance.classify_document = AsyncMock(
        return_value="Progress Note"
    )

    mock_analyzer_instance = mock_analyzer_cls.return_value
    mock_analyzer_instance.analyze_document = AsyncMock(
        return_value={"findings": [{"risk": "High"}]}
    )

    # Act
    with patch("src.core.analysis_service.get_settings", return_value=mock_settings):
        service = AnalysisService(retriever=MagicMock())
        result = await service.analyze_document(str(dummy_document), discipline="pt")

    # Assert
    mock_doc_classifier_instance.classify_document.assert_awaited_once()
    mock_analyzer_instance.analyze_document.assert_awaited_once()
    assert "analysis" in result
    assert result["analysis"]["findings"][0]["risk"] == "High"
