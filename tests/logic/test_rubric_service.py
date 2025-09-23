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

    ot_rules = service.get_filtered_rules("Unknown", discipline="ot")
    assert len(ot_rules) > 0
    for rule in ot_rules:
        assert rule.discipline == "ot"

    # Test Case 2: Filter by Document Type only (discipline is All)
    progress_note_rules = service.get_filtered_rules("Progress Note", discipline="All")
    assert len(progress_note_rules) > 0
    for rule in progress_note_rules:
        assert rule.document_type is None or rule.document_type == "Progress Note"

    # Test Case 3: Filter by both Document Type and Discipline
    slp_eval_rules = service.get_filtered_rules("Evaluation", discipline="slp")
    assert len(slp_eval_rules) > 0
    for rule in slp_eval_rules:
        assert rule.discipline == "slp"
        assert rule.document_type is None or rule.document_type == "Evaluation"
    assert any("Plan of Care may be incomplete" in r.issue_title for r in slp_eval_rules)

    # Test Case 4: "All" discipline should return all doc type matches
    all_discipline_pn_rules = service.get_filtered_rules("Progress Note", discipline="All")
    pt_discipline_pn_rules = service.get_filtered_rules("Progress Note", discipline="pt")
    # The "All" discipline should have at least as many rules as the "pt" discipline
    assert len(all_discipline_pn_rules) >= len(pt_discipline_pn_rules)
    assert any(r.discipline == "pt" for r in all_discipline_pn_rules)
    assert any(r.discipline == "ot" for r in all_discipline_pn_rules)
