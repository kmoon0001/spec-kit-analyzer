import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.guideline_service import GuidelineService
 
@pytest.fixture(scope="function")
def guideline_service():
    """Fixture to create a GuidelineService instance for testing."""
    # Clean up cache files before running the test
    cache_dir = "data"
    index_path = os.path.join(cache_dir, "guidelines.index")
    chunks_path = os.path.join(cache_dir, "guidelines.pkl")
    if os.path.exists(index_path):
        os.remove(index_path)
    if os.path.exists(chunks_path):
        os.remove(chunks_path)

    file_path = "test_data/static_guidelines.txt"
    return GuidelineService(sources=[file_path])

def test_load_and_index_guidelines(guideline_service):
    """
    Tests that guidelines can be loaded from a local file.
    """
    assert guideline_service.is_index_ready is True
    assert len(guideline_service.guideline_chunks) > 0

def test_search_found(guideline_service):
    """
    Tests that a search for an existing keyword returns results.
    """
    results = guideline_service.search("Medicare")

    assert len(results) > 0
    assert "medicare" in results[0]["text"].lower()

def test_search_not_found():
    """
    Tests that a search for a non-existing keyword returns no results.
    """
    # Initialize a new service with no sources
    guideline_service = GuidelineService(sources=[])
    results = guideline_service.search("nonexistentkeyword")

    assert len(results) == 0
