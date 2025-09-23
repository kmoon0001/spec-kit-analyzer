import os
import pytest
from src.parsing import parse_document_content, parse_document_into_sections

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
# The test_data directory is at the project root, so we need to go up two levels from tests/logic.
TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(TESTS_DIR)), "test_data")
VALID_TXT_PATH = os.path.join(TEST_DATA_DIR, "good_note_1.txt")
NON_EXISTENT_PATH = os.path.join(TEST_DATA_DIR, "non_existent_file.xyz")

def test_parse_document_content_with_valid_txt_file():
    """
    Tests parsing a standard .txt file.
    """
    sentences = parse_document_content(VALID_TXT_PATH)
    assert isinstance(sentences, list)
    assert len(sentences) > 0

    # Check the structure of the output
    first_sentence, first_source = sentences[0]
    assert isinstance(first_sentence, str)
    assert isinstance(first_source, str)
    assert first_source == "Text File"

    # Check that the content is roughly what we expect
    # We'll read the file directly to compare
    with open(VALID_TXT_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Reconstruct the parsed text
    parsed_text = " ".join([s for s, _ in sentences])
    # A simple check to see if the parsed text contains the core content
    assert "Patient seen for skilled therapy session" in parsed_text
    assert "The medical necessity of this treatment" in parsed_text

def test_parse_unsupported_file_type(tmp_path):
    """
    Tests that the parser handles an unsupported file type gracefully.
    """
    unsupported_file = tmp_path / "document.zip"
    unsupported_file.write_text("this is a zip file, in theory")

    result = parse_document_content(str(unsupported_file))
    assert len(result) == 1
    assert result[0][0].startswith("Error: Unsupported file type")
    assert result[0][1] == "File Handler"

def test_parse_non_existent_file():
    """
    Tests that the parser handles a non-existent file path correctly.
    """
    result = parse_document_content(NON_EXISTENT_PATH)
    assert len(result) == 1
    assert result[0][0].startswith("Error: File not found")
    assert result[0][1] == "File System"


def test_parse_document_into_sections_happy_path():
    """
    Tests that a well-formatted document is correctly parsed into sections.
    """
    document_text = """
Subjective: Patient reports feeling well.
Objective: Gait steady. Vital signs stable.
Assessment: Making good progress.
Plan: Continue with current treatment.
"""
    sections = parse_document_into_sections(document_text)
    assert isinstance(sections, dict)
    assert len(sections) == 4
    assert "Subjective" in sections
    assert "Plan" in sections
    assert sections["Objective"] == "Gait steady. Vital signs stable."

def test_parse_document_into_sections_no_headers():
    """
    Tests that a document with no section headers is handled correctly.
    """
    document_text = "This is a single block of text without any section headers."
    sections = parse_document_into_sections(document_text)
    assert isinstance(sections, dict)
    assert len(sections) == 1
    assert "unclassified" in sections
    assert sections["unclassified"] == document_text
