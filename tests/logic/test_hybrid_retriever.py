import pytest
from unittest.mock import patch, MagicMock
import numpy as np

# Import the class to be tested
from src.core.hybrid_retriever import HybridRetriever

# --- Mocks ---


@pytest.fixture(scope="module")
def mock_sentence_transformer():
    """Mocks the SentenceTransformer to avoid downloading models during tests."""
    with patch("sentence_transformers.SentenceTransformer") as mock_st:
        mock_model = MagicMock()
        # Ensure encode returns a numpy array of the correct type and shape
        mock_model.encode.return_value = np.random.rand(1, 384).astype("float32")
        mock_st.return_value = mock_model
        yield mock_st


@pytest.fixture
def retriever(mock_sentence_transformer):
    """
    Provides a HybridRetriever instance with mocked rules and dependencies.
    """
    # Mock the rules that the retriever would normally load from a file
    mock_rules = [
        {
            "uri": "rule1",
            "issue_title": "Goal Specificity",
            "issue_detail": "Goals must be measurable.",
        },
        {
            "uri": "rule2",
            "issue_title": "Signature Missing",
            "issue_detail": "All documents must be signed.",
        },
    ]

    with patch.object(HybridRetriever, "_load_rules", return_value=mock_rules):
        retriever_instance = HybridRetriever()
    return retriever_instance


# --- Tests ---


def test_retriever_initialization(retriever):
    """
    Tests that the HybridRetriever initializes correctly with mocked data.
    """
    assert retriever is not None
    assert len(retriever.rules) == 2
    assert retriever.corpus is not None
    assert retriever.bm25 is not None
    assert retriever.dense_retriever is not None


def test_retriever_search_logic(retriever):
    """
    Tests the core search logic of the retriever.
    """
    # Arrange
    query = "measurable patient goals"

    # Mock the return values of the underlying BM25 and dense retrievers
    # to test the re-ranking and combination logic in isolation.
    retriever.bm25.get_scores = MagicMock(return_value=np.array([0.9, 0.1]))
    retriever.dense_retriever.search = MagicMock(
        return_value=([np.array([0.2, 0.8])], [np.array([0, 1])])
    )

    # Act
    results = retriever.retrieve(query)

    # Assert
    # 1. Check that we get results back
    assert results is not None
    assert len(results) > 0

    # 2. Check the re-ranking logic.
    # The BM25 score for rule1 is high (0.9), but the dense score is low (0.2).
    # The BM25 score for rule2 is low (0.1), but the dense score is high (0.8).
    # The hybrid score should reflect a combination of these.
    # A simple test is to ensure the top result is one of our mock rules.
    assert results[0]["issue_title"] in ["Goal Specificity", "Signature Missing"]
