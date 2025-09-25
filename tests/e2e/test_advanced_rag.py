import pytest
from unittest.mock import MagicMock, patch
import json
import sys

# We need to mock the missing modules before importing the ComplianceAnalyzer
# so we do not import it at the top level of the file.
# from src.core.compliance_analyzer import ComplianceAnalyzer
from src.rubric_service import ComplianceRule
from src.document_classifier import DocumentType

@pytest.fixture
def mock_rules():
    """Provides a list of mock compliance rules for testing."""
    return [
        ComplianceRule(
            uri="http://example.com/rule/keyword",
            issue_title="Keyword Match Rule",
            issue_detail="This rule is designed to be found by keyword search. It contains the word 'signature'.",
            suggestion="N/A", severity="Low", strict_severity="Low", issue_category="Test", discipline="pt", document_type="Evaluation",
            financial_impact=0, positive_keywords=[], negative_keywords=[]
        ),
        ComplianceRule(
            uri="http://example.com/rule/specific",
            issue_title="Specific Goal Rule",
            issue_detail="Goals must be measurable and specific.",
            suggestion="Rewrite goals to be measurable.", severity="Medium", strict_severity="Medium", issue_category="Content", discipline="pt", document_type="Evaluation",
            financial_impact=0, positive_keywords=[], negative_keywords=[]
        )
    ]

@pytest.fixture
def compliance_analyzer(mocker, mock_rules):
    """
    Test fixture to create a ComplianceAnalyzer instance with mocked dependencies.
    This fixture ensures that expensive models and external services are mocked
    *before* the ComplianceAnalyzer is instantiated.
    """
    # Mock the missing modules to prevent ImportError
    mocker.patch.dict(sys.modules, {
        'src.core.ner': MagicMock(),
        'src.core.explanation': MagicMock(),
        'src.core.llm_service': MagicMock(),
        'src.core.prompt_manager': MagicMock(),
        'src.core.hybrid_retriever': MagicMock(),
        'ctransformers': MagicMock()
    })

    from src.core.compliance_analyzer import ComplianceAnalyzer

    # Create mock dependencies
    mock_guideline_service = MagicMock()
    mock_retriever = MagicMock()

    # Configure the retriever to return our mock rules
    mock_retriever.retrieve.return_value = mock_rules

    # Create a config dictionary
    config = {
        'models': {
            'ner_model': 'dummymodel',
            'prompt_template': 'dummy/template.txt',
            'llm_repo_id': 'dummymodel',
            'llm_filename': 'dummymodel'
        }
    }

    # Instantiate the real ComplianceAnalyzer with mocked dependencies
    analyzer = ComplianceAnalyzer(
        config=config,
        guideline_service=mock_guideline_service,
        retriever=mock_retriever
    )

    # Further mock methods on the instantiated object's dependencies
    analyzer.ner_pipeline.extract_entities.return_value = [{'entity_group': 'Test', 'word': 'test'}]
    analyzer.explanation_engine.add_explanations.side_effect = lambda analysis, rules: analysis
    mocker.patch.object(analyzer, '_format_rules_for_prompt', return_value="")

    return analyzer

def test_analyze_document_retrieves_rules(compliance_analyzer, mock_rules):
    """
    Verifies that the analyzer retrieves rules and returns them.
    """
    # Arrange
    document_text = "The therapist's signature is missing."
    discipline = "pt"
    doc_type = "Evaluation"

    # Configure the mock LLM to return a simple finding
    mock_llm_output = {"findings": [{"text": "signature missing"}]}
    compliance_analyzer.llm_service.generate_analysis.return_value = json.dumps(mock_llm_output)

    # Configure the retriever to return the mock rules
    compliance_analyzer.retriever.retrieve.return_value = mock_rules

    # Act
    analysis_results = compliance_analyzer.analyze_document(document_text, discipline, doc_type)

    # Assert
    compliance_analyzer.retriever.retrieve.assert_called_once()
    assert "findings" in analysis_results


def test_analyze_document_handles_no_findings(compliance_analyzer):
    """
    Verifies that the analyzer handles cases where the LLM returns no findings.
    """
    # Arrange
    document_text = "This document is perfect."
    discipline = "ot"
    doc_type = "Note"

    # Configure the mock LLM to return no findings
    mock_llm_output = {"findings": []}
    compliance_analyzer.llm_service.generate_analysis.return_value = json.dumps(mock_llm_output)

    # Configure the retriever to return no rules
    compliance_analyzer.retriever.retrieve.return_value = []

    # Act
    analysis_results = compliance_analyzer.analyze_document(document_text, discipline, doc_type)

    # Assert
    assert "findings" in analysis_results
    assert len(analysis_results["findings"]) == 0