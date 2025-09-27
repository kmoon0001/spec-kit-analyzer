import pytest
from unittest.mock import patch
import numpy as np


# Mock heavy dependencies at the module level before they are imported by the service
@pytest.fixture(autouse=True, scope="module")
def mock_heavy_dependencies():
    with patch("sentence_transformers.SentenceTransformer") as mock_st, patch(
        "faiss.IndexFlatL2"
    ) as mock_faiss_index, patch(
        "src.guideline_service.parse_guideline_file"
    ) as mock_parse:

        # Configure mocks
        mock_st.return_value.encode.return_value = np.random.rand(1, 384).astype(
            "float32"
        )
        mock_faiss_index.return_value.search.return_value = (
            np.array([[0.1]]),
            np.array([[0]]),
        )
        mock_parse.return_value = [
            {
                "summary": "Test summary about Medicare",
                "sentences": [
                    "Test sentence 1 about Medicare.",
                    "This is another sentence.",
                ],
                "source": "dummy_source.txt",
            }
        ]

        yield


# Import the service *after* the mocks are in place
from src.guideline_service import GuidelineService


@pytest.fixture
def guideline_service():
    """Provides a GuidelineService instance for testing with mocked dependencies."""
    service = GuidelineService(sources=["dummy_source.txt"])
    # Manually set the index as ready since _load_or_build_index is effectively mocked
    service.is_index_ready = True
    return service


def test_search_successful_orchestration(guideline_service: GuidelineService):
    """Tests that the search method correctly orchestrates the hierarchical search."""
    # Arrange
    query = "test query"

    # Act
    results = guideline_service.search(query)

    # Assert
    # 1. Check that the query was encoded
    guideline_service.model.encode.assert_called_with([query])

    # 2. Check that the hierarchical search was performed (summary -> final)
    guideline_service.summary_index.search.assert_called_once()
    guideline_service.faiss_index.search.assert_called_once()

    # 3. Check that the results are correctly formatted
    assert len(results) > 0
    assert "medicare" in results[0]["text"].lower()
    assert results[0]["source"] == "dummy_source.txt"


def test_search_returns_empty_if_index_not_ready(guideline_service: GuidelineService):
    """Tests that search returns an empty list if the index is not ready."""
    # Arrange
    guideline_service.is_index_ready = False

    # Act
    results = guideline_service.search("another query")

    # Assert
    assert results == []
