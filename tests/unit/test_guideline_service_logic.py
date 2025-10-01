import pytest
from unittest.mock import patch, MagicMock
import numpy as np
import sys

# No sys.path manipulation needed if pytest runs from the root

from src.core.guideline_service import GuidelineService


@pytest.fixture
def mock_heavy_dependencies():
    """Mocks faiss and SentenceTransformer to avoid heavy lifting."""
    # Mock the entire faiss module before it's imported by the service
    mock_faiss_module = MagicMock()
    mock_faiss_index = MagicMock()
    mock_faiss_index.search.return_value = (np.array([[0.1]]), np.array([[0]]))
    mock_faiss_module.IndexFlatL2.return_value = mock_faiss_index
    sys.modules["faiss"] = mock_faiss_module

    with patch("src.core.guideline_service.SentenceTransformer") as mock_st_class:
        mock_st_instance = MagicMock()
        mock_st_instance.encode.return_value = np.random.rand(1, 384).astype("float32")
        mock_st_class.return_value = mock_st_instance

        yield {"st_class": mock_st_class, "faiss_module": mock_faiss_module}

    # Clean up the mock from sys.modules
    del sys.modules["faiss"]


@pytest.fixture
def guideline_service(mock_heavy_dependencies):
    with patch.object(GuidelineService, "_load_or_build_index", return_value=None):
        service = GuidelineService(sources=["dummy_source.txt"])

    service.is_index_ready = True
    service.guideline_chunks = [
        ("Test sentence 1 about Medicare.", "dummy_source.txt"),
        ("This is another sentence.", "dummy_source.txt"),
    ]
    service.faiss_index = mock_heavy_dependencies["faiss_module"].IndexFlatL2()
    return service


def test_search_successful_orchestration(guideline_service: GuidelineService):
    query = "test query"
    results = guideline_service.search(query)
    # The search method calls encode without extra arguments for the query
    guideline_service.model.encode.assert_called_with([query], convert_to_tensor=True)
    guideline_service.faiss_index.search.assert_called_once()
    assert len(results) > 0
    assert "Test sentence 1 about Medicare." in results[0]["text"]
    assert results[0]["source"] == "dummy_source.txt"


def test_search_returns_empty_if_index_not_ready(guideline_service: GuidelineService):
    guideline_service.is_index_ready = False
    results = guideline_service.search("another query")
    assert results == []
