import sys
import os
import pytest
from unittest.mock import MagicMock

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

from core.ner import NERPipeline

# A more accurate mock for SpaCy's Token
class MockToken:
    def __init__(self, text, i):
        self.lower_ = text.lower()
        self.i = i

# A more accurate mock for SpaCy's Span, making it iterable
class MockSpan:
    def __init__(self, text, label_, start_char=0, end_char=0):
        self.text = text
        self.label_ = label_
        self.start_char = start_char
        self.end_char = end_char
        # Create mock tokens for the span
        self.tokens = [MockToken(t, i) for i, t in enumerate(text.split())]
        # Assign a mock 'i' to the span itself for window checking
        if self.tokens:
            self.start = self.tokens[0].i
            self.end = self.tokens[-1].i + 1
            # A mock 'i' for a token in the span, used for window checks
            self.i = self.tokens[0].i

    def __iter__(self):
        return iter(self.tokens)

# A more accurate mock for SpaCy's Doc
class MockDoc:
    def __init__(self, spans):
        self.ents = spans
        # Reconstruct the text and calculate char offsets for each span
        self.text = ""
        current_pos = 0
        for i, span in enumerate(spans):
            # Add a space between spans to mimic original text reconstruction
            if i > 0:
                self.text += " "
                current_pos += 1

            # Set character offsets for the span
            span.start_char = current_pos
            self.text += span.text
            span.end_char = len(self.text)
            current_pos = len(self.text)

        # Create a flat list of all tokens from all spans
        all_tokens = []
        token_offset = 0
        for span in self.ents:
            for i, token_text in enumerate(span.text.split()):
                all_tokens.append(MockToken(token_text, token_offset + i))
            token_offset += len(span.text.split())
        self.tokens = all_tokens

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.tokens[key.start:key.stop]
        return self.tokens[key]

    def char_span(self, start_char: int, end_char: int, label: str = "", alignment_mode: str = "strict"):
        """A simplified mock of SpaCy's char_span method."""
        span_text = self.text[start_char:end_char]
        if not span_text:
            return None
        return MockSpan(span_text, label, start_char, end_char)


@pytest.fixture
def ner_pipeline(mocker):
    """Returns an NERPipeline instance with a mocked SpaCy model."""
    mocker.patch("spacy.load", return_value=MagicMock())
    pipeline = NERPipeline(model_names=[])
    pipeline.spacy_nlp = MagicMock()
    return pipeline

def test_extract_clinician_with_keyword(ner_pipeline):
    """Test that a PERSON entity near a keyword is identified as a clinician."""
    text = "Signature: Dr. Jane Doe, PT"
    mock_doc = MockDoc([MockSpan("Signature:", "KEYWORD"), MockSpan("Dr. Jane Doe, PT", "PERSON")])
    ner_pipeline.spacy_nlp.return_value = mock_doc

    entities = ner_pipeline.extract_clinician_name(text)

    assert len(entities) == 1
    assert entities[0]["word"] == "Dr. Jane Doe"

def test_ignore_person_not_near_keyword(ner_pipeline):
    """Test that a PERSON entity not near a keyword is ignored."""
    text = "The patient, John Smith, reported improvement."
    mock_doc = MockDoc([MockSpan("John Smith", "PERSON")])
    ner_pipeline.spacy_nlp.return_value = mock_doc

    entities = ner_pipeline.extract_clinician_name(text)
    assert len(entities) == 0

def test_multiple_clinicians_found_and_deduplicated(ner_pipeline):
    """Test that multiple clinicians are found and deduplicated."""
    text = "Therapist: Dr. Emily White. Co-signed by: Michael Brown, COTA."
    mock_doc = MockDoc([
        MockSpan("Therapist:", "KEYWORD"),
        MockSpan("Dr. Emily White", "PERSON"),
        MockSpan("by:", "KEYWORD"),
        MockSpan("Michael Brown, COTA", "PERSON")
    ])
    ner_pipeline.spacy_nlp.return_value = mock_doc

    entities = ner_pipeline.extract_clinician_name(text)
    assert len(entities) == 2
    words = {e["word"] for e in entities}
    assert "Dr. Emily White" in words
    assert "Michael Brown" in words

def test_deduplication_of_same_name(ner_pipeline):
    """Test that the same name found twice is deduplicated."""
    text = "Signature: Sarah Connor. Later, the note was signed by Sarah Connor."
    mock_doc = MockDoc([
        MockSpan("Signature:", "KEYWORD"),
        MockSpan("Sarah Connor", "PERSON"),
        MockSpan("by", "KEYWORD"),
        MockSpan("Sarah Connor", "PERSON"),
    ])
    ner_pipeline.spacy_nlp.return_value = mock_doc

    entities = ner_pipeline.extract_clinician_name(text)
    assert len(entities) == 1
    assert entities[0]["word"] == "Sarah Connor"