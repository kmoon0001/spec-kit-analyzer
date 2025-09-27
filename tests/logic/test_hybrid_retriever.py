import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Import the class to be tested
from src.core.hybrid_retriever import HybridRetriever

# --- Mocks ---


@pytest.fixture(scope="function")
def mock_sentence_transformer():
    """Mocks the SentenceTransformer to avoid downloading models during tests."""
    with patch("src.core.hybrid_retriever.SentenceTransformer") as mock_st:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(2, 384).astype("float32")
        mock_st.return_value = mock_model
        yield mock_st


@pytest.fixture
def retriever(mock_sentence_transformer):
    """Provides a HybridRetriever instance with mocked rules and dependencies."""
    mock_rules = [
        {
            "id": 1,
            "name": "Goal Specificity",
            "content": "Goals must be measurable and specific.",
        },
        {
            "id": 2,
            "name": "Signature Missing",
            "content": "All documents must be signed by the therapist.",
        },
    ]

    with patch.object(HybridRetriever, "_load_rules_from_db", return_value=mock_rules):
        retriever_instance = HybridRetriever()
    return retriever_instance


# --- Tests ---


def test_retriever_initialization(retriever):
    """Tests that the HybridRetriever initializes correctly."""
    assert retriever is not None
    assert len(retriever.rules) == 2
    retriever.dense_retriever.encode.assert_called_once()


def test_retriever_search_logic(retriever):
    """Tests the core search logic of the retriever."""
    # Arrange
    query = "signed patient goals"
    retriever.bm25.get_scores = MagicMock(return_value=np.array([0.1, 0.9]))

    mock_tensor = MagicMock()
    mock_tensor.cpu.return_value.numpy.return_value = np.array([0.8, 0.2])

    with patch("src.core.hybrid_retriever.cos_sim", return_value=[mock_tensor]):
        # Act
        results = retriever.retrieve(query)

    # Assert
    assert results is not None
    assert len(results) > 0
    assert retriever.dense_retriever.encode.call_count == 2
    assert results[0]["name"] in ["Goal Specificity", "Signature Missing"]
