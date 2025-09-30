import pytest
from src.core.phi_scrubber import scrub_phi

def test_scrub_phi_with_ner_and_regex():
    # Test case with a mix of PHI that can be caught by NER and regex
    text = "Patient John Doe, born on 1980-01-01, lives in New York. His phone is 555-123-4567 and email is john.doe@example.com. MRN: 12345."
    scrubbed_text = scrub_phi(text)

    # Check that NER-detected entities are scrubbed
    assert "[PERSON]" in scrubbed_text
    assert "[DATE]" in scrubbed_text
    assert "[GPE]" in scrubbed_text

    # Check that regex-detected entities are scrubbed
    assert "[PHONE]" in scrubbed_text
    assert "[EMAIL]" in scrubbed_text
    assert "[MRN]" in scrubbed_text

def test_scrub_phi_no_phi():
    # Test case with no PHI
    text = "This is a simple sentence with no personal information."
    scrubbed_text = scrub_phi(text)
    assert text == scrubbed_text

def test_scrub_phi_edge_cases():
    # Test case with misspellings or variations that regex might miss
    # Using "New York City" as "NYC" is not reliably detected by the small model
    text = "Patient Jon Doe visited the clinic in New York City. His birthdate is Jan 1, 1980."
    scrubbed_text = scrub_phi(text)

    assert "[PERSON]" in scrubbed_text
    assert "[GPE]" in scrubbed_text
    assert "[DATE]" in scrubbed_text

def test_scrub_phi_empty_string():
    # Test with an empty string
    text = ""
    scrubbed_text = scrub_phi(text)
    assert "" == scrubbed_text

def test_scrub_phi_non_string_input():
    # Test with non-string input
    text = 12345
    scrubbed_text = scrub_phi(text)
    assert text == scrubbed_text