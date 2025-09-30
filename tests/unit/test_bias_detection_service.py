import unittest
from src.core.bias_detection_service import BiasDetectionService

class TestBiasDetectionService(unittest.TestCase):

    def setUp(self):
        self.config = {}
        self.service = BiasDetectionService(self.config)

    def test_detect_bias_with_biased_recommendation(self):
        """Test bias detection with a recommendation containing biased language"""
        findings = [
            {"suggestion": "This recommendation is for an elderly patient."},
            {"suggestion": "A neutral recommendation."},
        ]
        biased_findings = self.service.detect_bias(findings)
        self.assertEqual(len(biased_findings), 1)
        self.assertEqual(biased_findings[0]["bias_type"], "age")
        self.assertEqual(biased_findings[0]["keyword"], "elderly")

    def test_detect_bias_with_no_bias(self):
        """Test bias detection with no biased language"""
        findings = [
            {"suggestion": "A neutral recommendation."},
            {"suggestion": "Another neutral recommendation."},
        ]
        biased_findings = self.service.detect_bias(findings)
        self.assertEqual(len(biased_findings), 0)

if __name__ == '__main__':
    unittest.main()