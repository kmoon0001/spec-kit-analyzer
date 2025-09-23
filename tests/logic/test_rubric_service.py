import os
import pytest
from backend.app.rubric_service import RubricService, ComplianceRule

# Define the path to the test rubrics relative to this test file
# This makes the tests runnable from any directory
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up two directories from tests/logic to the project root, then into backend/app
BACKEND_APP_DIR = os.path.join(TESTS_DIR, "..", "..", "backend", "app")
VALID_RUBRIC_PATH = os.path.join(BACKEND_APP_DIR, "pt_compliance_rubric.ttl")
NON_EXISTENT_RUBRIC_PATH = os.path.join(BACKEND_APP_DIR, "non_existent_rubric.ttl")

def test_initialization_with_valid_rubric():
    """
    Tests that the RubricService initializes correctly with a valid ontology file.
    """
    service = RubricService(VALID_RUBRIC_PATH)
    assert service.graph is not None
    assert len(service.graph) > 0, "Graph should be populated after loading a valid rubric."

def test_get_rules_returns_list_of_compliance_rules():
    """
    Tests that get_rules() returns a list of ComplianceRule objects.
    """
    service = RubricService(VALID_RUBRIC_PATH)
    rules = service.get_rules()
    assert isinstance(rules, list)
    assert len(rules) > 0, "Should retrieve rules from the valid rubric."
    for rule in rules:
        assert isinstance(rule, ComplianceRule)

def test_retrieved_rule_has_correct_data():
    """
    Tests that the data within a retrieved ComplianceRule object is correct.
    This test is specific to the content of pt_compliance_rubric.ttl.
    """
    service = RubricService(VALID_RUBRIC_PATH)
    rules = service.get_rules()

    # Find a specific, known rule from the rubric to inspect
    # Example: The rule about missing signatures
    signature_rule = next((r for r in rules if "signature" in r.issue_title.lower()), None)

    assert signature_rule is not None, "Could not find the signature rule in the test rubric."
    assert signature_rule.severity == "finding"
    assert signature_rule.strict_severity == "flag"
    assert "Provider signature/date possibly missing" in signature_rule.issue_title
    assert signature_rule.issue_category == "Signatures/Dates"

    # Check that keywords are parsed correctly
    assert "signed" in signature_rule.negative_keywords
    assert "signature" in signature_rule.negative_keywords
    assert "dated" in signature_rule.negative_keywords
    assert len(signature_rule.positive_keywords) == 0

def test_initialization_with_non_existent_file():
    """
    Tests that the service handles a non-existent file path gracefully.
    It should not raise an exception, but the graph should be empty.
    """
    # We expect this to log an error, but not to crash the application.
    service = RubricService(NON_EXISTENT_RUBRIC_PATH)
    assert service.graph is not None
    assert len(service.graph) == 0, "Graph should be empty for a non-existent file."

    # Check that get_rules returns an empty list without error
    rules = service.get_rules()
    assert isinstance(rules, list)
    assert len(rules) == 0

def test_initialization_with_malformed_rubric(tmp_path):
    """
    Tests that the service handles a malformed .ttl file gracefully.
    """
    # Create a temporary malformed rubric file
    malformed_file = tmp_path / "malformed_rubric.ttl"
    malformed_file.write_text("this is not valid turtle syntax.")

    # We expect this to log an error, but not to crash.
    service = RubricService(str(malformed_file))
    assert service.graph is not None
    assert len(service.graph) == 0, "Graph should be empty for a malformed file."

    # Check that get_rules returns an empty list
    rules = service.get_rules()
    assert isinstance(rules, list)
    assert len(rules) == 0
