import pytest
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from src.guideline_service import GuidelineService

@pytest.fixture(scope="module")
def guideline_service():
    """
    Fixture to create a GuidelineService instance with a representative test document.
    This runs once per module, building the index from a controlled test file.
    """
    # Clear any cached index from previous runs to ensure a clean state
    index_path = "data/guidelines.index"
    chunks_path = "data/guidelines.pkl"
    if os.path.exists(index_path):
        os.remove(index_path)
    if os.path.exists(chunks_path):
        os.remove(chunks_path)

    # Create a representative test document
    sample_guideline_path = "tests/test_data/sample_guideline.txt"
    with open(sample_guideline_path, "w") as f:
        f.write("Physical therapy goals should be objective, measurable, and time-bound. This is essential for demonstrating skilled progress to Medicare.")

    # Initialize the service, which will build the index
    return GuidelineService(sources=[sample_guideline_path])

def test_initialization_and_indexing(guideline_service):
    """
    Tests that the GuidelineService initializes correctly and builds its search index.
    """
    assert guideline_service.is_index_ready is True, "FAISS index should be marked as ready."
    assert guideline_service.faiss_index.ntotal > 0, "FAISS index should contain vectors."
    assert len(guideline_service.guideline_chunks) > 0, "Guideline chunks should be loaded."

def test_semantic_search_relative_ranking(guideline_service):
    """
    Tests the core semantic search functionality using a relative ranking assertion.
    This is the industry-standard way to test a fuzzy, score-based retrieval system.
    It asserts that a relevant query gets a better score (lower distance) than an irrelevant one.
    """
    # A query that is semantically close to the content of the test document
    good_query = "Are the patient's goals measurable for Medicare?"

    # A query that is nonsensical and semantically distant
    bad_query = "the sky is made of green cheese and purple dragons"

    # Search for both queries
    good_results = guideline_service.search(good_query, top_k=1)
    bad_results = guideline_service.search(bad_query, top_k=1)

    # 1. Assert that the service returned a result for both queries
    assert len(good_results) > 0, "Search for a good query should return at least one result."
    assert len(bad_results) > 0, "A similarity search always returns the closest match, even if it's a bad one."

    # 2. Extract the scores (L2 Distance)
    good_score = good_results[0]["score"]
    bad_score = bad_results[0]["score"]

    # 3. The core assertion: A smaller score means a better match.
    # We assert that the relevant query is a much better match than the nonsensical one.
    assert good_score < bad_score, f"The score for a relevant query ({good_score}) should be lower than for an irrelevant one ({bad_score})."

    # 4. Optional: A sanity check on the content of the best match
    assert "medicare" in good_results[0]["text"].lower(), "The top result for the good query should contain the expected content."

def test_search_returns_empty_for_no_sources():
    """
    Tests that the service handles being initialized with no sources and returns an empty list.
    """
    # Clear any cached index from previous runs to ensure a clean state
    index_path = "data/guidelines.index"
    chunks_path = "data/guidelines.pkl"
    if os.path.exists(index_path):
        os.remove(index_path)
    if os.path.exists(chunks_path):
        os.remove(chunks_path)

    empty_service = GuidelineService(sources=[])
    results = empty_service.search("any query")
    assert results == [], "Search should return an empty list if no sources were provided."