import pytest
from unittest.mock import patch, mock_open
import os

# Import the functions to be tested
from src.utils import chunk_text, load_config


# --- Tests for chunk_text --- #

def test_chunk_text_simple():
    """Tests basic chunking functionality."""
    text = "a" * 100
    chunks = chunk_text(text, max_chars=50)
    assert len(chunks) == 2
    assert chunks[0] == "a" * 50
    assert chunks[1] == "a" * 50

def test_chunk_text_uneven():
    """Tests chunking with a final chunk smaller than max_chars."""
    text = "a" * 120
    chunks = chunk_text(text, max_chars=50)
    assert len(chunks) == 3
    assert chunks[0] == "a" * 50
    assert chunks[1] == "a" * 50
    assert chunks[2] == "a" * 20

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

# --- Tests for load_config --- #

@patch("src.utils.yaml.safe_load")
@patch("builtins.open", new_callable=mock_open, read_data="key: value")
def test_load_config_successfully(mock_safe_load, mock_file):
    """Tests that load_config correctly opens and parses the YAML file."""
    # Arrange
    mock_safe_load.return_value = {"key": "value"}
    # The utils file is in 'src/', so we go up one level.
    expected_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml'))
    
    # Act
    config = load_config()
    
    # Assert
    # Check that the function opened the correct file path
    mock_file.assert_called_once_with(expected_path, 'r')

    # Check that the yaml parser was called
    mock_safe_load.assert_called_once()
    # Check that the correct config was returned
    assert config == {"key": "value"}