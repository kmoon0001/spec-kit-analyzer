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
    llm_service.generate_analysis.return_value = '{"findings": []}'
    llm_service.parse_json_output.return_value = {"findings": []}

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
    compliance_analyzer.llm_service.generate_analysis.assert_called_once()
    compliance_analyzer.explanation_engine.add_explanations.assert_called_once()
    assert result == {"clinician_name": "Unknown", "findings": []}


def test_format_rules_for_prompt():
    rules = [
        {
            "issue_title": "Rule 1",
            "issue_detail": "Detail 1",
            "suggestion": "Suggestion 1",
        },
        {
            "issue_title": "Rule 2",
            "issue_detail": "Detail 2",
            "suggestion": "Suggestion 2",
        },
    ]

    context = ComplianceAnalyzer._format_rules_for_prompt(rules)

    assert "- **Rule:** Rule 1" in context
    assert "  **Detail:** Detail 1" in context
    assert "  **Suggestion:** Suggestion 1" in context
    assert "- **Rule:** Rule 2" in context
