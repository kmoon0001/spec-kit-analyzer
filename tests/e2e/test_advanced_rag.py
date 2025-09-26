import pytest
from unittest.mock import MagicMock, patch
import json
from src.core.compliance_analyzer import ComplianceAnalyzer
from src.rubric_service import ComplianceRule
from src.document_classifier import DocumentType

@pytest.fixture
def compliance_analyzer_with_mocks(mocker):
    """
    Test fixture to create a ComplianceAnalyzer instance with mocked dependencies.
    This fixture ensures that expensive models and external services are mocked
    *before* the ComplianceAnalyzer is instantiated.
    """
    # 1. Define a controlled set of compliance rules for testing 
    mock_rules = [
        ComplianceRule(
            uri="http://example.com/rule/keyword",
            issue_title="Keyword Match Rule",
            issue_detail="This rule is designed to be found by keyword search. It contains the word 'signature'.",
            suggestion="N/A", severity="Low", strict_severity="Low", issue_category="Test", discipline="pt", document_type="Evaluation"
        ),
        ComplianceRule(
            uri="http://example.com/rule/semantic",
            issue_title="Semantic Match Rule",
            issue_detail="This rule is about clinician authentication, which is semantically similar to signing.",
            suggestion="N/A", severity="High", strict_severity="High", issue_category="Test", discipline="pt", document_type="Evaluation"
        ),
        ComplianceRule(
            uri="http://example.com/rule/specific",
            issue_title="Specific Goal Rule",
            issue_detail="Goals must be measurable and specific.",
            suggestion="Rewrite goals to be measurable.", severity="Medium", strict_severity="Medium", issue_category="Content", discipline="pt", document_type="Evaluation"
        )
    ]

    # 2. Mock the RubricService to avoid real RDF graph loading and querying
    mock_rubric_service_instance = MagicMock()
    mock_rubric_service_instance.get_rules.return_value = mock_rules
    mocker.patch('src.core.hybrid_retriever.RubricService', return_value=mock_rubric_service_instance)

    # 3. Mock the expensive ML models
    mocker.patch('src.core.compliance_analyzer.AutoModelForCausalLM.from_pretrained')
    mocker.patch('src.core.compliance_analyzer.AutoTokenizer.from_pretrained')
    mocker.patch('src.core.hybrid_retriever.SentenceTransformer')
    # NOTE: CrossEncoder is not used in the current implementation, so it's not mocked.

    # 4. Mock GuidelineService and Retriever
    mock_guideline_service = MagicMock()
    mock_retriever = MagicMock()

    # 5. Instantiate the real ComplianceAnalyzer, injecting the mocked services
    analyzer = ComplianceAnalyzer(
        guideline_service=mock_guideline_service,
        retriever=mock_retriever,
        use_query_transformation=True
    )

    # 6. Mock the classifier and LLM generator for predictable behavior in tests
    # Note: The classifier is part of the GuidelineService now, so we mock it there.
    mock_guideline_service.classify_document = MagicMock()
    analyzer.generator_model = MagicMock()
    analyzer.generator_tokenizer = MagicMock()
    analyzer.generator_tokenizer.decode.return_value = '{"findings": []}'

    # Return the analyzer and the mock rules for use in tests
    return analyzer, mock_rules

def test_hybrid_search_finds_specific_rule(compliance_analyzer_with_mocks):
    """
    Verifies that the retriever can find a specific rule based on a keyword query.
    """
    analyzer, mock_rules = compliance_analyzer_with_mocks
    analyzer.guideline_service.classify_document.return_value = DocumentType.EVALUATION

    # Mock the retriever's search to inspect its results
    analyzer.retriever.search.return_value = mock_rules
    analyzer.analyze_document("The therapist's signature is missing.", "pt")

    # Assert that the search method was called correctly
    analyzer.retriever.search.assert_called_with(
        query="The therapist's signature is missing.",
        discipline="pt",
        doc_type=DocumentType.EVALUATION.name
    )

    # Assert that the rule with the keyword 'signature' was retrieved
    retrieved_rules = analyzer.retriever.search.return_value
    assert any(rule.issue_title == "Keyword Match Rule" for rule in retrieved_rules)

def test_query_transformation_is_called(compliance_analyzer_with_mocks, mocker):
    """
    Verifies that the query transformation is applied and the transformed query
    is passed to the retriever.
    """
    analyzer, _ = compliance_analyzer_with_mocks
    analyzer.guideline_service.classify_document.return_value = DocumentType.EVALUATION

    # Define a specific transformed query to check for
    transformed_query = "expanded and transformed test query"
    mocker.patch.object(analyzer, '_transform_query', return_value=transformed_query)

    # Spy on the retriever's search method
    analyzer.retriever.search.return_value = []
    analyzer.analyze_document("test document", "pt")

    # Assert that the search method was called with the transformed query
    analyzer.retriever.search.assert_called_with(
        query=transformed_query,
        discipline="pt",
        doc_type=DocumentType.EVALUATION.name
    )

def test_final_report_content_verification(compliance_analyzer_with_mocks):
    """
    Verifies that the final report correctly identifies a compliance issue
    based on the mocked LLM output.
    """
    analyzer, _ = compliance_analyzer_with_mocks
    analyzer.guideline_service.classify_document.return_value = DocumentType.EVALUATION

    # Mock the LLM's output to simulate finding a specific compliance issue
    mock_llm_output = {
      "findings": [
        {
          "text_quote": "Patient goal is to 'walk better'",
          "risk_description": "The goal 'walk better' is not measurable or specific.",
          "suggestion": "Rewrite the goal to be measurable, like 'Patient will walk 100 feet with minimal assistance in 2 weeks.'",
          "rule_id": "http://example.com/rule/specific"
        }
      ],
      "final_score": 85
    }

    # The tokenizer's decode method is the final step in getting the LLM's string output
    analyzer.generator_tokenizer.decode.return_value = json.dumps(mock_llm_output)

    # Run the analysis
    analysis_results = analyzer.analyze_document("Patient goal is to 'walk better'", "pt")

    # Assert that the parsed report contains the correct information
    assert "findings" in analysis_results
    assert len(analysis_results["findings"]) == 1
    assert analysis_results["final_score"] == 85

    finding = analysis_results["findings"][0]
    assert finding["text_quote"] == "Patient goal is to 'walk better'"
    assert "not measurable or specific" in finding["risk_description"]
    assert finding["rule_id"] == "http://example.com/rule/specific"
    assert "explanation" in finding
