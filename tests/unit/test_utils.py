import os
from unittest.mock import patch, mock_open

# Import the functions to be tested
from src.utils import chunk_text

# --- Tests for chunk_text --- #

def test_chunk_text_with_short_text():
    """Tests that text shorter than the max_chars is not chunked."""
    text = "This is a short text."
    chunks = chunk_text(text, max_chars=100)
    assert len(chunks) == 1
    assert chunks[0] == text

def test_chunk_text_with_long_text():
    """Tests that long text is correctly split into multiple chunks."""
    text = "a" * 250
    chunks = chunk_text(text, max_chars=100)
    assert len(chunks) == 3
    assert chunks[0] == "a" * 100
    assert chunks[1] == "a" * 100
    assert chunks[2] == "a" * 50

def test_chunk_text_respects_newlines():
    """Tests that chunking tries to split on newlines for cleaner breaks."""
    # Create text where a newline appears after a long first sentence.
    text = "a" * 150 + "\n" + "b" * 50
    # Set max_chars to be larger than the first sentence, but smaller than the whole text.
    chunks = chunk_text(text, max_chars=200)
    # It should split at the newline, not at the max_chars limit.
    assert len(chunks) == 2
    # The first chunk should end with the newline
    assert chunks[0] == "a" * 150 + "\n"
    assert chunks[1] == "b" * 50
