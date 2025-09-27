import pytest
from unittest.mock import patch

# Import the function to be tested
from src.core.smart_chunker import sentence_window_chunker


# Mock nltk.download to prevent network calls in any environment
@pytest.fixture(autouse=True, scope="module")
def mock_nltk_download():
    with patch("nltk.download") as mock_download:
        yield mock_download


# --- Test Cases ---


def test_empty_text():
    """Tests that the chunker returns an empty list for empty text."""
    assert sentence_window_chunker("") == []


def test_single_sentence():
    """Tests that a single sentence results in a single chunk with itself as the window."""
    text = "This is the only sentence."
    chunks = sentence_window_chunker(text)
    assert len(chunks) == 1
    assert chunks[0]["sentence"] == text
    assert chunks[0]["window"] == text


def test_multiple_sentences_with_window_size_one():
    """Tests the sliding window logic with a window size of 1."""
    text = "Sentence one. Sentence two. Sentence three."
    chunks = sentence_window_chunker(text, window_size=1)

    # Expected sentences
    s1 = "Sentence one."
    s2 = "Sentence two."
    s3 = "Sentence three."

    assert len(chunks) == 3

    # Check chunk for the first sentence (no preceding context)
    assert chunks[0]["sentence"] == s1
    assert chunks[0]["window"] == f"{s1} {s2}"

    # Check chunk for the middle sentence (context on both sides)
    assert chunks[1]["sentence"] == s2
    assert chunks[1]["window"] == f"{s1} {s2} {s3}"

    # Check chunk for the last sentence (no following context)
    assert chunks[2]["sentence"] == s3
    assert chunks[2]["window"] == f"{s2} {s3}"


def test_metadata_is_passed_through():
    """Tests that the metadata dictionary is correctly passed to each chunk."""
    text = "Sentence one. Sentence two."
    metadata = {"source": "test_doc.txt"}
    chunks = sentence_window_chunker(text, metadata=metadata)

    assert len(chunks) > 0
    for chunk in chunks:
        assert "source" in chunk["metadata"]
        assert chunk["metadata"]["source"] == "test_doc.txt"
