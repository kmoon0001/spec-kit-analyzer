import os
from unittest.mock import MagicMock, patch, mock_open

from src.parsing import parse_document_content, parse_document_into_sections

# --- Tests for parse_document_content --- #

@patch("src.parsing.os.path.exists", return_value=True)
@patch("src.parsing.pdfplumber.open")
def test_parse_pdf_content(mock_pdf_open, mock_exists):
    """Tests that the parser correctly calls the pdfplumber library for .pdf files."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "This is text from a PDF."
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf

    chunks = parse_document_content("fake/path/document.pdf")

    mock_pdf_open.assert_called_once_with("fake/path/document.pdf")
    assert len(chunks) > 0
    assert "This is text from a PDF" in chunks[0]['sentence']

@patch("src.parsing.os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data="This is a test from a txt file.")
def test_parse_txt_content(mock_file, mock_exists):
    """Tests parsing a .txt file using a mocked filesystem."""
    chunks = parse_document_content("fake/path/document.txt")

    mock_file.assert_called_once_with("fake/path/document.txt", "r", encoding="utf-8")
    assert len(chunks) > 0
    assert "This is a test from a txt file" in chunks[0]['sentence']

@patch("src.parsing.os.path.exists", return_value=False)
def test_parse_non_existent_file(mock_exists):
    """Tests that the parser handles a non-existent file gracefully."""
    result = parse_document_content("non_existent_file.txt")

    assert len(result) == 1
    assert result[0]['sentence'].startswith("Error: File not found")

@patch("src.parsing.os.path.exists", return_value=True)
def test_parse_unsupported_file_type(mock_exists):
    """Tests that the parser handles an unsupported file type."""
    result = parse_document_content("document.zip")
    assert len(result) == 1
    assert result[0]['sentence'].startswith("Error: Unsupported file type")

# --- Tests for parse_document_into_sections --- #

def test_parse_document_into_sections_happy_path():
    """Tests that a well-formatted document is correctly parsed into sections."""
    document_text = (
        "Subjective: Patient reports feeling well.\n"
        "Objective: Gait steady. Vital signs stable.\n"
        "Assessment: Making good progress.\n"
        "Plan: Continue with current treatment.\n"
    )
    sections = parse_document_into_sections(document_text)
    assert isinstance(sections, dict)
    assert len(sections) == 4
    assert "Subjective" in sections
    assert sections["Objective"] == "Gait steady. Vital signs stable."

def test_parse_document_into_sections_no_headers():
    """Tests that a document with no section headers is handled correctly."""
    document_text = "This is a single block of text without any section headers."
    sections = parse_document_into_sections(document_text)
    assert isinstance(sections, dict)
    assert len(sections) == 1
    assert "unclassified" in sections
    assert sections["unclassified"] == document_text