import unittest
from unittest.mock import patch, MagicMock
from src.core.phi_scrubber import PhiScrubberService

# Mock Span class to simulate spaCy's Span objects
class MockSpan:
    def __init__(self, text, label_, start_char, end_char):
        self.text = text
        self.label_ = label_
        self.start_char = start_char
        self.end_char = end_char

    def __repr__(self):
        return f"MockSpan(text='{self.text}', label_='{self.label_}')"

# Mock Doc class to simulate spaCy's Doc objects
class MockDoc:
    def __init__(self, text, ents):
        self.text = text
        self.ents = ents

class TestPhiScrubberService(unittest.TestCase):

    def setUp(self):
        # This mock will be applied to all tests in this class
        self.spacy_patch = patch('spacy.load')
        self.mock_spacy_load = self.spacy_patch.start()

        # Configure the mock nlp object
        self.mock_nlp = MagicMock()
        self.mock_spacy_load.return_value = self.mock_nlp

    def tearDown(self):
        self.spacy_patch.stop()

    def test_scrub_text_with_label_style(self):
        """Test PHI scrubbing with 'label' style redaction"""
        config = {"redaction_style": "label", "ner_labels": ["PERSON", "DATE"]}
        scrubber = PhiScrubberService(config)

        text = "Patient John Doe visited on 01/01/2023."
        # Define the entities that the mock nlp model will return
        mock_ents = [
            MockSpan("John Doe", "PERSON", 8, 16),
            MockSpan("01/01/2023", "DATE", 28, 38)
        ]
        self.mock_nlp.return_value = MockDoc(text, mock_ents)

        expected_text = "Patient [PERSON] visited on [DATE]."
        self.assertEqual(scrubber.scrub_text(text), expected_text)

    def test_scrub_text_with_placeholder_style(self):
        """Test PHI scrubbing with 'placeholder' style redaction"""
        config = {"redaction_style": "placeholder", "ner_labels": ["PERSON", "DATE"]}
        scrubber = PhiScrubberService(config)

        text = "Patient John Doe visited on 01/01/2023."
        mock_ents = [
            MockSpan("John Doe", "PERSON", 8, 16),
            MockSpan("01/01/2023", "DATE", 28, 38)
        ]
        self.mock_nlp.return_value = MockDoc(text, mock_ents)

        expected_text = "Patient [REDACTED] visited on [REDACTED]."
        self.assertEqual(scrubber.scrub_text(text), expected_text)

    def test_scrub_text_with_custom_labels(self):
        """Test PHI scrubbing with custom NER labels"""
        config = {"redaction_style": "label", "ner_labels": ["GPE"]}
        scrubber = PhiScrubberService(config)

        text = "The patient lives in New York."
        mock_ents = [
            MockSpan("New York", "GPE", 21, 29)
        ]
        self.mock_nlp.return_value = MockDoc(text, mock_ents)

        expected_text = "The patient lives in [GPE]."
        self.assertEqual(scrubber.scrub_text(text), expected_text)

if __name__ == '__main__':
    unittest.main()