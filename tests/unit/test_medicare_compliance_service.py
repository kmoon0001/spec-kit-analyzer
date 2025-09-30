import unittest
from src.core.medicare_compliance_service import MedicareComplianceService

class TestMedicareComplianceService(unittest.TestCase):

    def setUp(self):
        self.config = {}
        self.service = MedicareComplianceService(self.config)

    def test_score_document_with_no_findings(self):
        """Test scoring with no findings, expecting a perfect score"""
        findings = []
        score_details = self.service.score_document(findings)
        self.assertEqual(score_details["score"], 100)
        self.assertEqual(score_details["deductions"], 0)

    def test_score_document_with_findings(self):
        """Test scoring with a mix of findings"""
        findings = [
            {"rule_id": "signature_rule"},
            {"rule_id": "goals_rule"},
            {"rule_id": "unknown_rule"}, # A non-specific finding
        ]
        score_details = self.service.score_document(findings)

        # signature_rule (15) + goals_rule (10) + unknown_rule (5) = 30 deductions
        expected_deductions = 30
        total_possible_score = sum(rule["weight"] for rule in self.service.medicare_rules.values())
        expected_score = int(((total_possible_score - expected_deductions) / total_possible_score) * 100)

        self.assertEqual(score_details["deductions"], expected_deductions)
        self.assertEqual(score_details["score"], expected_score)
        self.assertIn("signature_rule", score_details["violated_rules"])
        self.assertIn("goals_rule", score_details["violated_rules"])

if __name__ == '__main__':
    unittest.main()