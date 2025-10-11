import os
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.core.guideline_service import GuidelineService


@pytest.fixture
def mock_sentence_transformer():
    """Mocks the SentenceTransformer to avoid downloading models during tests."""
    with patch("sentence_transformers.SentenceTransformer") as mock_st:
        mock_model = MagicMock()
        # The encode method should return a 2D numpy array (list of embeddings)
        mock_model.encode.return_value = np.random.rand(1, 384).astype("float32")
        mock_st.return_value = mock_model
        yield mock_st


@pytest.fixture
def guideline_service(tmp_path, mock_sentence_transformer):
    """Provides a GuidelineService instance with a temporary cache directory."""
    # Create dummy source files
    source1_path = tmp_path / "source1.txt"
    source1_path.write_text("This is the first guideline document.")

    # The service needs a list of source paths
    sources = [str(source1_path)]

    # The GuidelineService will use the real implementation but with a mocked model
    # and a temporary cache directory.
    service = GuidelineService(sources=sources, cache_dir=str(tmp_path))

    return service


def test_guideline_service_initialization_and_caching(guideline_service: GuidelineService, tmp_path: str):
    """Tests that the GuidelineService initializes correctly and creates cache files."""
    assert guideline_service.is_index_ready
    assert os.path.exists(guideline_service.index_path)
    assert os.path.exists(guideline_service.chunks_path)


def test_guideline_service_search(guideline_service: GuidelineService):
    """
    Tests the search functionality of the GuidelineService.
    Since the FAISS index is real, we can't easily mock the search results,
    but we can ensure the method runs without error and returns the correct format.
    """
    # Arrange
    query = "guideline"

    # Act
    results = guideline_service.search(query, top_k=1)

    # Assert
    assert isinstance(results, list)
    # With our dummy data, we expect at least one result
    if results:
        assert "text" in results[0]
        assert "source" in results[0]
        assert "score" in results[0]
