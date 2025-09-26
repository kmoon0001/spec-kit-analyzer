import pytest
from unittest.mock import MagicMock

from src.core.compliance_analyzer import ComplianceAnalyzer

def test_analyze_document_orchestration(compliance_analyzer: ComplianceAnalyzer):
    """
    Tests that the ComplianceAnalyzer correctly orchestrates its components.
    """
    # Arrange
    document_text = "Patient requires assistance with transfers."
    discipline = "PT"
    doc_type = "Progress Note"

    # Act
    result = compliance_analyzer.analyze_document(document_text, discipline, doc_type)

    # Assert
    # Check that the main components were called, verifying orchestration
    compliance_analyzer.retriever.retrieve.assert_called_once()
    compliance_analyzer.ner_pipeline.extract_entities.assert_called_once_with(document_text)
    compliance_analyzer.prompt_manager.build_prompt.assert_called_once()
    compliance_analyzer.llm_service.generate_analysis.assert_called_once()
    compliance_analyzer.explanation_engine.add_explanations.assert_called_once()

def test_format_rules_for_prompt(compliance_analyzer: ComplianceAnalyzer):
    """Tests the construction of the rules context for the prompt."""
    rules = [
        {"id": 1, "name": "Test Rule 1", "content": "This is a test rule."},
        {"id": 2, "name": "Test Rule 2", "content": "This is another test rule."}
    ]

    # Access the private method for testing purposes
    context = compliance_analyzer._format_rules_for_prompt(rules)

    assert "Title: Test Rule 1, Content: This is a test rule." in context
    assert "Title: Test Rule 2, Content: This is another test rule." in context