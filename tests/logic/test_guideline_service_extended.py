import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.guideline_service import GuidelineService

@pytest.fixture
def guideline_service():
    """Fixture to create a GuidelineService instance."""
    return GuidelineService()

def test_load_and_index_guidelines(guideline_service):
    """
    Tests that guidelines can be loaded from a local file.
    """
    # Create a dummy guideline file
    file_path = "test_data/static_guidelines.txt"

    guideline_service.load_and_index_guidelines([file_path])

    assert guideline_service.is_index_ready is True
    assert len(guideline_service.guideline_chunks) > 0

def test_search_found(guideline_service):
    """
    Tests that a search for an existing keyword returns results.
    """
    file_path = "test_data/static_guidelines.txt"
    guideline_service.load_and_index_guidelines([file_path])

    results = guideline_service.search("Medicare")

    assert len(results) > 0
    assert "medicare" in results[0]["text"].lower()

def test_search_not_found(guideline_service):
    """
    Tests that a search for a non-existing keyword returns no results.
    """
    file_path = "test_data/static_guidelines.txt"
    guideline_service.load_and_index_guidelines([file_path])

    results = guideline_service.search("nonexistentkeyword")

    assert len(results) == 0
