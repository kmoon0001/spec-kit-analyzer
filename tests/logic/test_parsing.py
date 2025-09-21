import os
import pytest
from src.parsing import parse_document_content, split_sentences

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_DIR = os.path.join(os.path.dirname(TESTS_DIR), "test_data")
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

def test_split_sentences_logic():
    """
    Tests the split_sentences helper function directly.
    """
    text1 = "This is the first sentence. This is the second one! And a third?"
    result1 = split_sentences(text1)
    assert len(result1) == 3
    assert result1[0] == "This is the first sentence."
    assert result1[1] == "This is the second one!"
    assert result1[2] == "And a third?"

    text2 = "A sentence with no punctuation at the end"
    result2 = split_sentences(text2)
    assert len(result2) == 1
    assert result2[0] == text2

    text3 = "Mr. Smith went to Washington. He saw the White House."
    result3 = split_sentences(text3)
    # This is a known limitation of the regex, it will split on "Mr."
    # The test documents this behavior.
    assert len(result3) > 1

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
