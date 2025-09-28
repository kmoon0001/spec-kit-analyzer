import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.analysis_service import AnalysisService


@pytest.fixture
def dummy_document(tmp_path):
    doc_path = tmp_path / "test_document.txt"
    doc_path.write_text(
        "The patient shows improvement but lacks quantifiable progress.",
        encoding="utf-8",
    )
    return doc_path


@pytest.mark.asyncio
@patch("src.core.analysis_service.ComplianceAnalyzer")
@patch("src.core.analysis_service.DocumentClassifier")
@patch("src.core.analysis_service.PromptManager")
@patch("src.core.analysis_service.ExplanationEngine")
@patch("src.core.analysis_service.NERPipeline")
@patch("src.core.analysis_service.FactCheckerService")
@patch("src.core.analysis_service.NLGService")
@patch("src.core.analysis_service.LLMService")
@patch("src.core.analysis_service.get_settings")
async def test_full_analysis_pipeline(
    mock_get_settings,
    mock_llm_service_cls,
    mock_nlg_service_cls,
    mock_fact_checker_cls,
    mock_ner_cls,
    mock_explanation_cls,
    mock_prompt_manager_cls,
    mock_document_classifier_cls,
    mock_compliance_analyzer_cls,
    dummy_document,
):
    """Ensure AnalysisService orchestrates dependencies as expected."""
    prompt_manager_instance = MagicMock()
    prompt_manager_instance.build_prompt.return_value = "Prompt"
    mock_prompt_manager_cls.return_value = prompt_manager_instance

    llm_service_instance = mock_llm_service_cls.return_value
    llm_service_instance.is_ready.return_value = True

    mock_nlg_service_cls.return_value.generate_personalized_tip.return_value = "Tip"

    document_classifier_instance = mock_document_classifier_cls.return_value
    document_classifier_instance.classify_document.return_value = "Progress Note"

    analyzer_instance = mock_compliance_analyzer_cls.return_value
    analyzer_instance.analyze_document = AsyncMock(
        return_value={"findings": [{"risk": "High"}]}
    )

    mock_get_settings.return_value = SimpleNamespace(
        models=SimpleNamespace(
            generator="repo",
            generator_filename="model.gguf",
            fact_checker="fc",
            ner_ensemble=["ner"],
            doc_classifier_prompt="tests/data/doc_classifier_prompt.txt",
            analysis_prompt_template="tests/data/analysis_prompt.txt",
            nlg_prompt_template="tests/data/nlg_prompt.txt",
        ),
        llm_settings=SimpleNamespace(dict=lambda: {"generation_params": {}}),
    )

    os.makedirs("tests/data", exist_ok=True)
    with open("tests/data/doc_classifier_prompt.txt", "w", encoding="utf-8") as f:
        f.write("Classify: {document_text}")
    with open("tests/data/analysis_prompt.txt", "w", encoding="utf-8") as f:
        f.write("Analyze: {document}\nContext: {context}")
    with open("tests/data/nlg_prompt.txt", "w", encoding="utf-8") as f:
        f.write("Tip for {issue_title}: {issue_detail}")

    service = AnalysisService(retriever=MagicMock())
    result = await service.analyze_document(str(dummy_document), discipline="pt")

    document_classifier_instance.classify_document.assert_called_once()
    analyzer_instance.analyze_document.assert_awaited_once()
    assert result["findings"][0]["risk"] == "High"
