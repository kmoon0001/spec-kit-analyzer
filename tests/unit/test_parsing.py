from unittest.mock import patch, mock_open, MagicMock

from src.core.parsing import parse_document_content, parse_document_into_sections


@patch("src.core.parsing.cache_service.set_to_disk")
@patch("src.core.parsing.cache_service.get_from_disk", return_value=None)
@patch("src.core.parsing._get_file_hash", return_value="pdfhash")
@patch("src.core.parsing.os.path.exists", return_value=True)
@patch("src.core.parsing.pdfplumber.open")
def test_parse_pdf_content(mock_pdf_open, mock_exists, mock_hash, mock_get_cache, mock_set_cache):
    """Tests that the parser correctly calls the pdfplumber library for .pdf files."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "This is text from a PDF."
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf

    chunks = parse_document_content("fake/path/document.pdf")

    mock_pdf_open.assert_called_once_with("fake/path/document.pdf")
    assert len(chunks) > 0
    assert "This is text from a PDF" in chunks[0]["sentence"]


@patch("src.core.parsing.cache_service.set_to_disk")
@patch("src.core.parsing.cache_service.get_from_disk", return_value=None)
@patch("src.core.parsing._get_file_hash", return_value="txthash")
@patch("src.core.parsing.os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data="This is a test from a txt file.")
def test_parse_txt_content(mock_file, mock_path_exists, mock_hash, mock_get_cache, mock_set_cache):
    chunks = parse_document_content("fake/path/document.txt")

    mock_file.assert_any_call("fake/path/document.txt", "r", encoding="utf-8")
    assert len(chunks) > 0
    assert "This is a test from a txt file" in chunks[0]["sentence"]


@patch("src.core.parsing.os.path.exists", return_value=False)
def test_parse_non_existent_file(mock_exists):
    result = parse_document_content("non_existent_file.txt")

    assert len(result) == 1
    assert "Error: File not found" in result[0]["sentence"]


@patch("src.core.parsing.os.path.exists", return_value=True)
def test_parse_unsupported_file_type(mock_exists):
    result = parse_document_content("document.zip")
    assert len(result) == 1
    assert "Error: Unsupported file type" in result[0]["sentence"]


def test_parse_document_into_sections_happy_path():
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
    assert sections["Objective"] == "Gait steady. Vital signs stable."


def test_parse_document_into_sections_no_headers():
    document_text = "This is a single block of text without any section headers."
    sections = parse_document_into_sections(document_text)
    assert isinstance(sections, dict)
    assert len(sections) == 1
    assert "unclassified" in sections
    assert sections["unclassified"] == document_text
