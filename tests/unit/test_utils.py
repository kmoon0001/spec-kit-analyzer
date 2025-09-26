import os
from unittest.mock import patch, mock_open

from src.utils import chunk_text, load_config

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
    text = "a" * 150 + "\n" + "b" * 50
    chunks = chunk_text(text, max_chars=200)
    assert len(chunks) == 2
    assert chunks[0] == "a" * 150
    assert chunks[1] == "b" * 50

# --- Tests for load_config --- #

@patch("builtins.open", new_callable=mock_open, read_data="key: value")
@patch("src.utils.yaml.safe_load")
def test_load_config_successfully(mock_safe_load, mock_file):
    """Tests that load_config correctly opens and parses the YAML file."""
    mock_safe_load.return_value = {"key": "value"}
    config = load_config()
    
    # The path is now calculated inside the function, so we just check that open was called.
    mock_file.assert_called()
    mock_safe_load.assert_called_once()
    assert config == {"key": "value"}