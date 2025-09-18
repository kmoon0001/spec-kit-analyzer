import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.text_chunking import RecursiveCharacterTextSplitter

def test_simple_split():
    splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10, keep_separator=False)
    text = "This is a test sentence. This is another test sentence. And a third one."
    chunks = splitter.split_text(text)
    assert len(chunks) == 2
    assert chunks[0] == "This is a test sentence. This is another test"
    assert chunks[1] == "test sentence. And a third one."

def test_no_split():
    splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)
    text = "This is a test sentence."
    chunks = splitter.split_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text

def test_split_with_newlines():
    splitter = RecursiveCharacterTextSplitter(chunk_size=30, chunk_overlap=5, keep_separator=False)
    text = "First line.\nSecond line.\nThird line."
    chunks = splitter.split_text(text)
    assert len(chunks) == 2
    assert chunks[0] == "First line.\nSecond line."
    assert chunks[1] == "Third line."

def test_long_text_split():
    splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
    text = "a" * 300
    chunks = splitter.split_text(text)
    assert len(chunks) == 4

def test_chunk_overlap():
    splitter = RecursiveCharacterTextSplitter(chunk_size=35, chunk_overlap=15, keep_separator=False)
    text = "This is a longer sentence to test the overlapping functionality of the text splitter."
    chunks = splitter.split_text(text)
    assert len(chunks) == 4

def test_invalid_config():
    with pytest.raises(ValueError):
        RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=20)
