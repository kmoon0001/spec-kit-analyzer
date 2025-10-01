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
    def __init__(self, text, i, head=None):
        self.lower_ = text.lower()
        self.i = i
        self.text = text
        self.head = head if head is not None else self

# A more accurate mock for SpaCy's Span, making it iterable
class MockSpan:
    def __init__(self, text, label_, start_char=0, end_char=0, tokens=None):
        self.text = text
        self.label_ = label_
        self.start_char = start_char
        self.end_char = end_char
        # Create mock tokens for the span
        self.tokens = tokens if tokens is not None else [MockToken(t, i) for i, t in enumerate(text.split())]
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
    def __init__(self, spans, all_tokens=None):
        self.ents = spans
        self.text = " ".join([span.text for span in spans])
        self.tokens = all_tokens if all_tokens is not None else []

        # Set head attributes for tokens within spans
        for span in self.ents:
            for i, token in enumerate(span.tokens):
                if i > 0:
                    token.head = span.tokens[i-1]
                else:
                    token.head = token # First token in span points to itself by default

    def __call__(self, text):
        # This allows the mock to be called like a spacy_nlp object
        # For simplicity, we'll just return self, assuming entities are pre-set
        return self

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
    # Mock the spacy_nlp object to return a callable MockDoc
    pipeline.spacy_nlp = MagicMock(return_value=MockDoc([]))  # Default empty doc
    return pipeline

def test_extract_clinician_with_keyword(ner_pipeline):
    """Test that a PERSON entity near a keyword is identified as a clinician."""
    text = "Signature: Dr. Jane Doe, PT"
    # Create tokens with appropriate heads
    token_signature = MockToken("Signature:", 0)
    token_dr = MockToken("Dr.", 1, head=token_signature)
    token_jane = MockToken("Jane", 2, head=token_dr)
    token_doe = MockToken("Doe,", 3, head=token_jane)
    token_pt = MockToken("PT", 4, head=token_doe)

    # Create a span for the person entity
    span_jane_doe = MockSpan("Dr. Jane Doe", "PERSON", tokens=[token_dr, token_jane, token_doe])

    mock_doc_instance = MockDoc(spans=[span_jane_doe], all_tokens=[token_signature, token_dr, token_jane, token_doe, token_pt])
    mock_doc_instance.text = text # Set the text attribute
    ner_pipeline.spacy_nlp.return_value = mock_doc_instance

    entities = ner_pipeline.extract_clinician_name(text)

    assert len(entities) == 1
    assert entities[0] == "Dr. Jane Doe"

def test_ignore_person_not_near_keyword(ner_pipeline):
    """Test that a PERSON entity not near a keyword is ignored."""
    text = "The patient, John Smith, reported improvement."
    # Create tokens with appropriate heads
    token_the = MockToken("The", 0)
    token_patient = MockToken("patient,", 1, head=token_the)
    token_john = MockToken("John", 2, head=token_patient)
    token_smith = MockToken("Smith,", 3, head=token_john)
    token_reported = MockToken("reported", 4, head=token_smith)
    token_improvement = MockToken("improvement.", 5, head=token_reported)

    # Create a span for the person entity
    span_john_smith = MockSpan("John Smith", "PERSON", tokens=[token_john, token_smith])

    mock_doc_instance = MockDoc(spans=[span_john_smith], all_tokens=[token_the, token_patient, token_john, token_smith, token_reported, token_improvement])
    mock_doc_instance.text = text # Set the text attribute
    ner_pipeline.spacy_nlp.return_value = mock_doc_instance

    entities = ner_pipeline.extract_clinician_name(text)
    assert len(entities) == 0

def test_multiple_clinicians_found_and_deduplicated(ner_pipeline):
    """Test that multiple clinicians are found and deduplicated."""
    text = "Therapist: Dr. Emily White. Co-signed by: Michael Brown, COTA."
    # Create tokens with appropriate heads
    token_therapist = MockToken("Therapist:", 0)
    token_dr = MockToken("Dr.", 1, head=token_therapist)
    token_emily = MockToken("Emily", 2, head=token_dr)
    token_white = MockToken("White.", 3, head=token_emily)
    token_co_signed = MockToken("Co-signed", 4)
    token_by = MockToken("by:", 5, head=token_co_signed)
    token_michael = MockToken("Michael", 6, head=token_by)
    token_brown = MockToken("Brown,", 7, head=token_michael)
    token_cota = MockToken("COTA.", 8, head=token_brown)

    # Create spans for the person entities
    span_emily_white = MockSpan("Dr. Emily White", "PERSON", tokens=[token_dr, token_emily, token_white])
    span_michael_brown = MockSpan("Michael Brown", "PERSON", tokens=[token_michael, token_brown])

    mock_doc_instance = MockDoc(spans=[span_emily_white, span_michael_brown], all_tokens=[token_therapist, token_dr, token_emily, token_white, token_co_signed, token_by, token_michael, token_brown, token_cota])
    mock_doc_instance.text = text # Set the text attribute
    ner_pipeline.spacy_nlp.return_value = mock_doc_instance

    entities = ner_pipeline.extract_clinician_name(text)
    assert len(entities) == 2
    assert "Dr. Emily White" in entities
    assert "Michael Brown" in entities

def test_deduplication_of_same_name(ner_pipeline):
    """Test that the same name found twice is deduplicated."""
    text = "Signature: Sarah Connor. Later, the note was signed by Sarah Connor."
    # Create tokens with appropriate heads
    token_signature = MockToken("Signature:", 0)
    token_sarah1 = MockToken("Sarah", 1, head=token_signature)
    token_connor1 = MockToken("Connor.", 2, head=token_sarah1)
    token_later = MockToken("Later,", 3)
    token_note = MockToken("note", 4, head=token_later)
    token_signed = MockToken("signed", 5, head=token_note)
    token_by = MockToken("by", 6, head=token_signed)
    token_sarah2 = MockToken("Sarah", 7, head=token_by)
    token_connor2 = MockToken("Connor.", 8, head=token_sarah2)

    # Create spans for the person entities
    span_sarah_connor1 = MockSpan("Sarah Connor", "PERSON", tokens=[token_sarah1, token_connor1])
    span_sarah_connor2 = MockSpan("Sarah Connor", "PERSON", tokens=[token_sarah2, token_connor2])

    mock_doc_instance = MockDoc(spans=[span_sarah_connor1, span_sarah_connor2], all_tokens=[token_signature, token_sarah1, token_connor1, token_later, token_note, token_signed, token_by, token_sarah2, token_connor2])
    mock_doc_instance.text = text # Set the text attribute
    ner_pipeline.spacy_nlp.return_value = mock_doc_instance

    entities = ner_pipeline.extract_clinician_name(text)
    assert len(entities) == 1
    assert entities[0] == "Sarah Connor"
