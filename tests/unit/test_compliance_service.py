import unittest
from unittest.mock import MagicMock
from src.core.compliance_service import ComplianceService
from src.core.models import TherapyDocument, ComplianceRule

class TestComplianceService(unittest.TestCase):

    def setUp(self):
        # Create mock rules for testing different scenarios
        self.rule_signature = ComplianceRule(
            uri="test:sig", severity="high", strict_severity="high", issue_title="Missing Signature",
            issue_detail="", issue_category="", discipline="pt", document_type="any",
            suggestion="", financial_impact=100,
            negative_keywords=["signature", "signed"]
        )

        self.rule_goals = ComplianceRule(
            uri="test:goals", severity="medium", strict_severity="medium", issue_title="Vague Goals",
            issue_detail="", issue_category="", discipline="pt", document_type="Progress Note",
            suggestion="", financial_impact=50,
            positive_keywords=["goal"],
            negative_keywords=["measurable", "specific"]
        )

        self.all_rules = [self.rule_signature, self.rule_goals]

        # We initialize the service by directly injecting the mock rules
        self.service = ComplianceService(rules=self.all_rules)


    def test_finding_for_missing_required_keyword(self):
        """Test finding is triggered when a required keyword (negative only) is missing."""
        # This document should only trigger the signature rule.
        doc = TherapyDocument(id="1", text="Patient feels better.", discipline="pt", document_type="Evaluation")
        result = self.service.evaluate_document(doc)
        self.assertFalse(result.is_compliant)
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0].rule.uri, self.rule_signature.uri)

    def test_no_finding_when_required_keyword_present(self):
        """Test no finding is triggered when a required keyword is present."""
        # This document contains a signature keyword, so it should be compliant.
        doc = TherapyDocument(id="1", text="The document is signed by the therapist.", discipline="pt", document_type="Evaluation")
        result = self.service.evaluate_document(doc)
        self.assertTrue(result.is_compliant)
        self.assertEqual(len(result.findings), 0)

    def test_finding_for_positive_and_negative_keywords(self):
        """Test finding is triggered for a rule with positive and negative keywords."""
        # This doc has a signature to satisfy the first rule, but triggers the goals rule.
        doc = TherapyDocument(id="1", text="The patient's goal is to improve walking. Signed by therapist.", discipline="pt", document_type="Progress Note")
        result = self.service.evaluate_document(doc)
        self.assertFalse(result.is_compliant)
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0].rule.uri, self.rule_goals.uri)

    def test_no_finding_when_negative_keyword_is_present_for_positive_rule(self):
        """Test no finding when a negative keyword is present for a positive keyword rule."""
        # This document satisfies both rules and should be compliant.
        doc = TherapyDocument(id="1", text="The patient's goal is to improve walking. This is a measurable goal. Signed by therapist.", discipline="pt", document_type="Progress Note")
        result = self.service.evaluate_document(doc)
        self.assertTrue(result.is_compliant)
        self.assertEqual(len(result.findings), 0)

    def test_no_finding_for_unrelated_discipline(self):
        """Test no findings for a document from a discipline with no rules."""
        doc = TherapyDocument(id="1", text="Patient feels better.", discipline="ot", document_type="Evaluation")
        result = self.service.evaluate_document(doc)
        self.assertTrue(result.is_compliant)

    def test_document_type_mismatch(self):
        """Test that rules are not applied if the document type does not match."""
        # The goals rule only applies to "Progress Note", so this should only trigger the signature rule.
        doc = TherapyDocument(id="1", text="The patient's goal is to improve walking.", discipline="pt", document_type="Evaluation")
        result = self.service.evaluate_document(doc)
        # We expect only the signature finding, not the goal finding.
        self.assertFalse(result.is_compliant)
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0].rule.uri, self.rule_signature.uri)


if __name__ == '__main__':
    unittest.main()