import unittest
from src.core.quality_assurance_service import QualityAssuranceService

class TestQualityAssuranceService(unittest.TestCase):

    def setUp(self):
        self.config = {}
        self.service = QualityAssuranceService(self.config)

    def test_check_consistency_with_inconsistent_findings(self):
        """Test consistency check with inconsistent findings"""
        entities = [{"normalized_term": "Pain"}]
        findings = [{"suggestion": "Work on strengthening."}]

        issues = self.service.check_consistency(entities, findings)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["entity"], "Pain")
        expected_issue = "The clinical finding 'Pain' was identified, but no related recommendation was found."
        self.assertEqual(issues[0]["issue"], expected_issue)

    def test_check_consistency_with_consistent_findings(self):
        """Test consistency check with consistent findings"""
        entities = [{"normalized_term": "Pain"}]
        findings = [{"suggestion": "Provide pain management."}]

        issues = self.service.check_consistency(entities, findings)

        self.assertEqual(len(issues), 0)

    def test_check_consistency_with_no_relevant_entities(self):
        """Test consistency check with no relevant entities"""
        entities = [{"normalized_term": "Other"}]
        findings = [{"suggestion": "Some recommendation."}]

        issues = self.service.check_consistency(entities, findings)

        self.assertEqual(len(issues), 0)

if __name__ == '__main__':
    unittest.main()