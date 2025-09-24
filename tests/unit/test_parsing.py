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
    chunks = parse_document_content(VALID_TXT_PATH)
    assert isinstance(chunks, list)
    assert len(chunks) > 0

    # Check the structure of the output
    first_chunk = chunks[0]
    assert isinstance(first_chunk, dict)
    assert "sentence" in first_chunk
    assert "window" in first_chunk
    assert "metadata" in first_chunk
    assert first_chunk['metadata']['source_document'] == VALID_TXT_PATH

    # Check that the content is roughly what we expect
    parsed_text = " ".join([chunk['sentence'] for chunk in chunks])
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
    assert result[0]['sentence'].startswith("Error: Unsupported file type")
    assert result[0]['metadata']['source'] == "File Handler"

def test_parse_non_existent_file():
    """
    Tests that the parser handles a non-existent file path correctly.
    """
    result = parse_document_content(NON_EXISTENT_PATH)
    assert len(result) == 1
    assert result[0]['sentence'].startswith("Error: File not found")
    assert result[0]['metadata']['source'] == "File System"


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
