import pytest
from unittest.mock import MagicMock

from src.core.compliance_analyzer import ComplianceAnalyzer


@pytest.fixture
def compliance_analyzer() -> ComplianceAnalyzer:
    """Provides a ComplianceAnalyzer instance with all dependencies mocked."""
    return ComplianceAnalyzer(
        retriever=MagicMock(),
        ner_pipeline=MagicMock(),
        llm_service=MagicMock(),
        explanation_engine=MagicMock(),
        prompt_manager=MagicMock(),
        fact_checker_service=MagicMock(),
    )


def test_analyze_document_orchestration(compliance_analyzer: ComplianceAnalyzer):
    """Tests that the ComplianceAnalyzer correctly orchestrates its components."""
    # Arrange
    document_text = "Patient requires assistance with transfers."
    discipline = "PT"
    doc_type = "Progress Note"

    # Mock the return values of the dependencies
    compliance_analyzer.retriever.retrieve_rules.return_value = []
    compliance_analyzer.ner_pipeline.extract_entities.return_value = ["transfers"]
    compliance_analyzer.prompt_manager.build_prompt.return_value = "Test Prompt"
    compliance_analyzer.llm_service.generate_text.return_value = '{"findings": []}'
    compliance_analyzer.llm_service.parse_json_output.return_value = {"findings": []}
    compliance_analyzer.explanation_engine.explain_findings.return_value = {
        "findings": []
    }

    # Act
    result = compliance_analyzer.analyze_document(document_text, discipline, doc_type)

    # Assert
    # Check that the main components were called in the correct sequence
    compliance_analyzer.retriever.retrieve_rules.assert_called_once_with(
        document_text, discipline=discipline, doc_type=doc_type
    )
    compliance_analyzer.ner_pipeline.extract_entities.assert_called_once_with(
        document_text
    )
    compliance_analyzer.prompt_manager.build_prompt.assert_called_once()
    compliance_analyzer.llm_service.generate_text.assert_called_once_with("Test Prompt")
    compliance_analyzer.explanation_engine.explain_findings.assert_called_once()
    # Check that the post-processing step was called by checking one of its sub-components
    compliance_analyzer.fact_checker_service.is_finding_plausible.assert_not_called()  # No findings in this case


def test_format_rules_for_prompt():
    """Tests the static method for formatting rules into a prompt string."""
    # Arrange
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

    # Act
    # Access the static method directly from the class
    context = ComplianceAnalyzer._format_rules_for_prompt(rules)

    # Assert
    assert "- **Rule:** Rule 1" in context
    assert "  **Detail:** Detail 1" in context
    assert "  **Suggestion:** Suggestion 1" in context
    assert "- **Rule:** Rule 2" in context
