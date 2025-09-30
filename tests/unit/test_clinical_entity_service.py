import unittest
from src.core.clinical_entity_service import ClinicalEntityService

class TestClinicalEntityService(unittest.TestCase):

    def setUp(self):
        self.config = {}
        self.service = ClinicalEntityService(self.config)

    def test_extract_and_normalize_entities(self):
        """Test extraction and normalization of clinical entities"""
        text = "The patient reports pain and decreased rom. We will work on strengthening."
        entities = self.service.extract_and_normalize_entities(text)

        normalized_terms = {e["normalized_term"] for e in entities}

        self.assertIn("Pain", normalized_terms)
        self.assertIn("Range of Motion", normalized_terms)
        self.assertIn("Strength", normalized_terms)

    def test_no_entities_found(self):
        """Test that no entities are returned when none are present"""
        text = "This is a generic sentence without any clinical terms."
        entities = self.service.extract_and_normalize_entities(text)
        self.assertEqual(len(entities), 0)

if __name__ == '__main__':
    unittest.main()