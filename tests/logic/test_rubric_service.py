import os
import pytest
from src.rubric_service import RubricService, ComplianceRule

# No longer need to define paths as the service loads all rubrics by default.

def test_initialization_with_valid_rubric():
    """
    Tests that the RubricService initializes correctly.
    """
    service = RubricService()
    assert service.graph is not None
    assert len(service.graph) > 0, "Graph should be populated after loading a valid rubric."

def test_get_rules_returns_list_of_compliance_rules():
    """
    Tests that get_rules() returns a list of ComplianceRule objects.
    """
    service = RubricService()
    rules = service.get_rules()
    assert isinstance(rules, list)
    assert len(rules) > 0, "Should retrieve rules from the valid rubric."
    for rule in rules:
        assert isinstance(rule, ComplianceRule)

def test_retrieved_rule_has_correct_data():
    """
    Tests that the data within a retrieved ComplianceRule object is correct.
    """
    service = RubricService()
    rules = service.get_rules()

    # Find a specific, known rule from the rubric to inspect
    signature_rule = next((r for r in rules if "signature" in r.issue_title.lower()), None)

    assert signature_rule is not None, "Could not find the signature rule in the test rubric."
    assert signature_rule.severity == "finding"
    assert signature_rule.strict_severity == "flag"
    assert "Provider signature/date possibly missing" in signature_rule.issue_title
    assert signature_rule.issue_category == "Signatures/Dates"
    assert "signed" in signature_rule.negative_keywords

def test_get_rules_for_document_type():
    """
    Tests that the filtering by document type works correctly.
    """
    service = RubricService()

    # Test for "Progress Note"
    progress_note_rules = service.get_rules_for_document_type("Progress Note")
    assert len(progress_note_rules) > 0
    for rule in progress_note_rules:
        assert rule.document_type is None or rule.document_type == "Progress Note"
    assert any("Goals may not be measurable" in r.issue_title for r in progress_note_rules)

    # Test for "Evaluation"
    evaluation_rules = service.get_rules_for_document_type("Evaluation")
    assert len(evaluation_rules) > 0
    for rule in evaluation_rules:
        assert rule.document_type is None or rule.document_type == "Evaluation"
    # Check that a specific "Evaluation" rule is present
    assert any("Plan of Care may be incomplete" in r.issue_title for r in evaluation_rules)
    # Check that a specific "Progress Note" rule is NOT present
    assert not any("Goals may not be measurable" in r.issue_title for r in evaluation_rules)

    # Test for "Unknown"
    unknown_rules = service.get_rules_for_document_type("Unknown")
    all_rules = service.get_rules()
    assert len(unknown_rules) == len(all_rules)
