import os
from unittest.mock import patch, mock_open

from src.utils import chunk_text

def test_chunk_text_with_short_text():
    text = "This is a short text."
    chunks = chunk_text(text, max_chars=100)
    assert len(chunks) == 1
    assert chunks[0] == text

def test_chunk_text_with_long_text():
    text = "a" * 250
    chunks = chunk_text(text, max_chars=100)
    assert len(chunks) == 3
    assert chunks[0] == "a" * 100
    assert chunks[1] == "a" * 100
    assert chunks[2] == "a" * 50