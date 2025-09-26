import pytest
from unittest.mock import patch, MagicMock
import numpy as np


# Mock heavy dependencies at the module level before they are imported by any service.
# The patch targets are now pointing to where the objects are *used*, not where they are defined.
@pytest.fixture(autouse=True, scope="module")
def mock_heavy_dependencies():
    with (
        patch("src.guideline_service.SentenceTransformer") as mock_st,
        patch("src.guideline_service.faiss") as mock_faiss,
        patch("src.guideline_service.parse_guideline_file") as mock_parse,
    ):
        # Configure mock instances and their methods
        mock_model_instance = MagicMock()
        mock_model_instance.encode.return_value = np.random.rand(1, 384).astype(
            "float32"
        )
        mock_st.return_value = mock_model_instance

        mock_faiss_index_instance = MagicMock()
        mock_faiss_index_instance.search.return_value = (
            np.array([[0.1]]),
            np.array([[0]]),
        )
        mock_faiss.IndexFlatL2.return_value = mock_faiss_index_instance

        mock_parse.return_value = [
            {"text": "Test sentence 1 about Medicare.", "source": "dummy_source.txt"}
        ]

        yield {"st_mock": mock_st, "faiss_mock": mock_faiss, "parse_mock": mock_parse}


# We only import the service after the mocks are in place.
@pytest.fixture
def guideline_service():
    """Provides a GuidelineService instance for testing with mocked dependencies."""
    from src.guideline_service import GuidelineService

    service = GuidelineService(sources=["dummy_source.txt"])
    # Manually set the index as ready since _load_or_build_index is effectively mocked
    service.is_index_ready = True
    # The test expects a list of tuples, so we mock the chunks attribute
    service.guideline_chunks = [("medicare test", "dummy_source.txt")]
    # Manually create a mock for the faiss_index, as it's not created when chunks are empty.
    service.faiss_index = MagicMock()
    # Configure the search method to return the correct tuple structure
    service.faiss_index.search.return_value = (np.array([[0.1]]), np.array([[0]]))
    return service


def test_search_successful_orchestration(guideline_service: "GuidelineService"):
    """
    Tests that the search method correctly orchestrates the search process.
    """
    # Arrange
    query = "test query"

    # Act
    results = guideline_service.search(query)

    # Assert
    # 1. Check that the query was encoded by the mocked model
    guideline_service.model.encode.assert_called_with([query], convert_to_tensor=True)

    # 2. Check that the FAISS index was searched
    guideline_service.faiss_index.search.assert_called_once()

    # 3. Check that the results are correctly formatted
    assert len(results) > 0
    assert "medicare" in results[0]["text"].lower()
    assert results[0]["source"] == "dummy_source.txt"


def test_search_returns_empty_if_index_not_ready(guideline_service: "GuidelineService"):
    """
    Tests that search returns an empty list if the index is not ready.
    """
    # Arrange
    guideline_service.is_index_ready = False

    # Act
    results = guideline_service.search("another query")

    # Assert
    assert results == []
