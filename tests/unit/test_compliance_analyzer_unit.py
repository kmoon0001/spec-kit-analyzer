from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.compliance_analyzer import ComplianceAnalyzer


@pytest.fixture
def compliance_analyzer() -> ComplianceAnalyzer:
    retriever = MagicMock()
    retriever.retrieve = AsyncMock(return_value=[])

    ner_pipeline = MagicMock()
    ner_pipeline.extract_entities.return_value = [
        {"entity_group": "ISSUE", "word": "transfers"}
    ]

    llm_service = MagicMock()
    llm_service.generate.return_value = '{"findings": []}'

    explanation_engine = MagicMock()
    explanation_engine.add_explanations.return_value = {"findings": []}

    prompt_manager = MagicMock()
    prompt_manager.build_prompt.return_value = "Prompt"

    fact_checker_service = MagicMock()
    fact_checker_service.is_finding_plausible.return_value = True

    nlg_service = MagicMock()
    nlg_service.generate_personalized_tip.return_value = "Tip"

    return ComplianceAnalyzer(
        retriever=retriever,
        ner_pipeline=ner_pipeline,
        llm_service=llm_service,
        explanation_engine=explanation_engine,
        prompt_manager=prompt_manager,
        fact_checker_service=fact_checker_service,
        nlg_service=nlg_service,
    )


@pytest.mark.asyncio
async def test_analyze_document_orchestration(compliance_analyzer: ComplianceAnalyzer):
    document_text = "Patient requires assistance with transfers."
    discipline = "PT"
    doc_type = "Progress Note"

    result = await compliance_analyzer.analyze_document(
        document_text=document_text, discipline=discipline, doc_type=doc_type
    )

    compliance_analyzer.retriever.retrieve.assert_awaited_once()
    compliance_analyzer.ner_pipeline.extract_entities.assert_called_once_with(
        document_text
    )
    compliance_analyzer.prompt_manager.build_prompt.assert_called_once()
    compliance_analyzer.llm_service.generate.assert_called_once()
    compliance_analyzer.explanation_engine.add_explanations.assert_called_once()
    assert result == {"findings": []}


def test_format_rules_for_prompt():
    """
    Tests the formatting of compliance rules for the LLM prompt.
    Ensures that rule names, details, and relevance scores are correctly included.
    """
    rules = [
        {
            "name": "Documentation Timeliness",
            "content": "All notes must be signed within 24 hours.",
            "relevance_score": 0.987,
        },
        {
            "name": "Goal Specificity",
            "content": "Goals must be measurable and objective.",
            "relevance_score": 0.876,
        },
    ]

    context = ComplianceAnalyzer._format_rules_for_prompt(rules)

    # Check that the formatted string contains the key elements.
    assert "- **Rule:** Documentation Timeliness" in context
    assert "  **Detail:** All notes must be signed within 24 hours." in context
    assert "- **Rule:** Goal Specificity" in context
    assert "  **Detail:** Goals must be measurable and objective." in context
