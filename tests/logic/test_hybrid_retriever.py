import pytest
from unittest.mock import patch, MagicMock
import numpy as np

from src.core.hybrid_retriever import HybridRetriever

@pytest.fixture(scope="module")
def mock_sentence_transformer():
    """Mocks the SentenceTransformer to avoid downloading models during tests."""
    with patch('sentence_transformers.SentenceTransformer') as mock_st:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(2, 384).astype('float32')
        mock_st.return_value = mock_model
        yield mock_st

@pytest.fixture
def retriever(mock_sentence_transformer):
    """
    Provides a HybridRetriever instance with mocked rules and dependencies.
    """
    mock_rubric_1 = MagicMock()
    mock_rubric_1.id = 1
    mock_rubric_1.name = 'Goal Specificity'
    mock_rubric_1.content = 'Goals must be measurable.'

    mock_rubric_2 = MagicMock()
    mock_rubric_2.id = 2
    mock_rubric_2.name = 'Signature Missing'
    mock_rubric_2.content = 'All documents must be signed.'

    mock_rules_from_db = [mock_rubric_1, mock_rubric_2]
    
    with patch('src.core.hybrid_retriever.crud.get_rubrics', return_value=mock_rules_from_db):
        retriever_instance = HybridRetriever()

    return retriever_instance

def test_retriever_initialization(retriever: HybridRetriever):
    """
    Tests that the HybridRetriever initializes correctly with mocked data.
    """
    assert retriever is not None
    assert len(retriever.rules) == 2
    assert len(retriever.corpus) == 2
    assert retriever.bm25 is not None
    assert retriever.dense_retriever is not None
    assert retriever.corpus_embeddings is not None
    assert retriever.corpus_embeddings.shape[0] == 2

def test_retriever_search_logic(retriever: HybridRetriever):
    """
    Tests the core search logic of the retriever.
    """
    query = "measurable patient goals"
    retriever.bm25.get_scores = MagicMock(return_value=np.array([0.9, 0.1]))

    with patch('src.core.hybrid_retriever.cos_sim') as mock_cos_sim:
        mock_cos_sim.return_value = np.array([[0.2, 0.8]])
        results = retriever.retrieve(query, top_k=1)

    assert results is not None
    assert len(results) == 1
    assert results[0]['name'] in ['Goal Specificity', 'Signature Missing']