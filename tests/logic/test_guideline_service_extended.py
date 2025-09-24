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
    # Use a dummy source file for testing
    dummy_source = "test_data/static_guidelines.txt"
    return GuidelineService(sources=[dummy_source])

def test_load_and_index_guidelines(guideline_service):
    """
    Tests that the GuidelineService initializes and loads the index.
    """
    assert guideline_service.is_index_ready is True
    assert len(guideline_service.sections_data) > 0

def test_search_found(guideline_service):
    """
    Tests that a search for an existing keyword returns results.
    """
    results = guideline_service.search("Medicare")
    assert len(results) > 0
    assert "medicare" in results[0]["text"].lower()

def test_search_not_found(guideline_service):
    """
    Tests that a search for a non-existing keyword returns no results.
    """
    results = guideline_service.search("nonexistentkeywordasdfghjkl", distance_threshold=0.5)
    assert len(results) == 0
