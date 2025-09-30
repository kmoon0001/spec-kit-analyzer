import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Import the class to be tested
from src.core.hybrid_retriever import HybridRetriever

# --- Mocks ---


@pytest.fixture
def retriever():
    """Provides a HybridRetriever instance with mocked dependencies."""
    with patch.object(HybridRetriever, "__init__", lambda s, rules=None: None):
        retriever_instance = HybridRetriever()
        retriever_instance.rules = [
            {
                "id": 1,
                "name": "Goal Specificity",
                "regulation": "Goals must be measurable.",
                "common_pitfalls": "Vague goals.",
                "best_practice": "Use SMART goals.",
            },
            {
                "id": 2,
                "name": "Signature Missing",
                "regulation": "All documents must be signed.",
                "common_pitfalls": "Forgetting to sign.",
                "best_practice": "Sign immediately after writing.",
            },
        ]
        retriever_instance.dense_retriever = MagicMock()
        retriever_instance.dense_retriever.encode.return_value = np.random.rand(
            2, 384
        ).astype("float32")
        retriever_instance.bm25 = MagicMock()
        retriever_instance.corpus_embeddings = np.random.rand(2, 384).astype(
            "float32"
        )
        yield retriever_instance


# --- Tests ---


def test_retriever_initialization(retriever):
    """Tests that the HybridRetriever initializes correctly."""
    assert retriever is not None
    assert len(retriever.rules) == 2


def test_retriever_search_logic(retriever):
    """Tests the core search logic of the retriever."""
    # Arrange
    query = "signed patient goals"
    retriever.bm25.get_scores.return_value = np.array([0.1, 0.9])

    mock_tensor = MagicMock()
    mock_tensor.cpu.return_value.numpy.return_value = np.array([0.8, 0.2])

    with patch("sentence_transformers.util.cos_sim", return_value=[mock_tensor]):
        # Act
        results = retriever.retrieve(query)

    # Assert
    assert results is not None
    assert len(results) > 0
    retriever.dense_retriever.encode.assert_called_once_with(query, convert_to_tensor=True)
    assert results[0]["name"] in ["Goal Specificity", "Signature Missing"]
