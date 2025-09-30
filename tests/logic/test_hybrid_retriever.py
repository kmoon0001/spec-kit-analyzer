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
        # Mock the three calls to encode(): one for the corpus (init) and two for the queries (retrieve).
        mock_model.encode.side_effect = [
            np.random.rand(3, 384).astype("float32"),  # Corpus embeddings
            np.random.rand(384).astype("float32"),    # Query embedding for first retrieve
            np.random.rand(384).astype("float32"),    # Query embedding for second retrieve
        ]
        mock_st.return_value = mock_model
        yield mock_st


@pytest.fixture
def retriever(mock_sentence_transformer):
    """Provides a HybridRetriever instance with mocked rules and dependencies."""
    mock_rules = [
        {"id": 1, "name": "Doc A", "content": "The quick brown fox."},
        {"id": 2, "name": "Doc B", "content": "Jumps over the lazy dog."},
        {"id": 3, "name": "Doc C", "content": "And lived happily ever after."},
    ]

    with patch.object(HybridRetriever, "_load_rules_from_db", return_value=mock_rules):
        retriever_instance = HybridRetriever()
        # Mock the BM25 get_scores method on the instance for direct control in tests.
        retriever_instance.bm25.get_scores = MagicMock()
    return retriever_instance


# --- Tests ---


def test_retriever_initialization(retriever):
    """Tests that the HybridRetriever initializes correctly."""
    assert retriever is not None
    assert len(retriever.rules) == 3
    # The mock is called once during initialization to build corpus embeddings.
    retriever.dense_retriever.encode.assert_called_once()


@pytest.mark.asyncio
async def test_rrf_ranking_logic(retriever):
    """
    Tests that the Reciprocal Rank Fusion (RRF) logic correctly combines
    and re-ranks the results from the two different retrievers.
    """
    # Arrange
    query = "some test query"

    # Mock BM25 scores to produce the rank order: A > B > C
    retriever.bm25.get_scores.return_value = np.array([0.9, 0.5, 0.1])

    # Mock dense retrieval scores to produce the rank order: C > A > B
    mock_dense_scores = np.array([0.5, 0.1, 0.9])
    mock_tensor = MagicMock()
    mock_tensor.cpu.return_value.numpy.return_value = mock_dense_scores

    # With these rankings, the expected RRF order is A > C > B.
    # This is because A is ranked high by both, while C is high in one but low in the other.

    with patch("src.core.hybrid_retriever.cos_sim", return_value=[mock_tensor]):
        # Act
        results = await retriever.retrieve(query, top_k=3)

    # Assert
    assert results is not None
    assert len(results) == 3

    result_names = [res["name"] for res in results]
    expected_order = ["Doc A", "Doc C", "Doc B"]

    assert result_names == expected_order, f"Expected {expected_order}, but got {result_names}"

    # Also test that top_k works correctly
    with patch("src.core.hybrid_retriever.cos_sim", return_value=[mock_tensor]):
        results_top_2 = await retriever.retrieve(query, top_k=2)

    assert len(results_top_2) == 2
    assert [res["name"] for res in results_top_2] == ["Doc A", "Doc C"]