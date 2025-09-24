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

def test_get_filtered_rules():
    """
    Tests that filtering by document type and discipline works correctly.
    """
    service = RubricService()

    # Test Case 1: Filter by Discipline only (doc_type is Unknown)
    pt_rules = service.get_filtered_rules("Unknown", discipline="pt")
    assert len(pt_rules) > 0
    for rule in pt_rules:
        assert rule.discipline == "pt"
