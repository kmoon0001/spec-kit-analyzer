import pytest
from unittest.mock import patch, MagicMock
import numpy as np

# Import the class to be tested
from src.core.hybrid_retriever import HybridRetriever

def test_retriever_initialization():
    """
    Tests that the HybridRetriever initializes correctly, mocking all external dependencies.
    """
    mock_rules = [
        {'id': 1, 'name': 'Rule 1', 'content': 'Content 1'},
        {'id': 2, 'name': 'Rule 2', 'content': 'Content 2'},
    ]

    # Use a context manager to ensure mocks are active only during this test
    with patch('src.core.hybrid_retriever.SentenceTransformer') as mock_st_class, \
         patch.object(HybridRetriever, '_load_rules_from_db', return_value=mock_rules):

        # Configure the mock instance that the SentenceTransformer class will return
        mock_instance = MagicMock()
        mock_instance.encode.return_value = np.random.rand(2, 384).astype('float32')
        mock_st_class.return_value = mock_instance

        # Act: Instantiate the class under test. Its __init__ will use the mocks.
        # We pass a mock for the database session.
        retriever = HybridRetriever(db=MagicMock())

        # Assert
        assert retriever is not None
        assert len(retriever.rules) == 2
        # The .encode() method should have been called once during initialization
        mock_instance.encode.assert_called_once()

def test_retriever_search_logic():
    """
    Tests the core hybrid search logic, mocking all external dependencies.
    """
    mock_rules = [
        {'id': 1, 'name': 'Goal Specificity', 'content': 'Goals must be measurable and specific.'},
        {'id': 2, 'name': 'Signature Missing', 'content': 'All documents must be signed by the therapist.'},
    ]

    with patch('src.core.hybrid_retriever.SentenceTransformer') as mock_st_class, \
         patch.object(HybridRetriever, '_load_rules_from_db', return_value=mock_rules), \
         patch('src.core.hybrid_retriever.cos_sim') as mock_cos_sim:

        # --- Arrange ---

        # 1. Configure the mock for SentenceTransformer
        mock_instance = MagicMock()
        # The first call to encode happens in __init__
        mock_instance.encode.return_value = np.random.rand(2, 384).astype('float32')
        mock_st_class.return_value = mock_instance

        # 2. Configure the mock for the similarity calculation
        mock_tensor = MagicMock()
        mock_tensor.cpu.return_value.numpy.return_value = np.array([0.8, 0.2])
        mock_cos_sim.return_value = [mock_tensor]

        # --- Act ---

        # 3. Instantiate the retriever. This will call encode() once.
        retriever = HybridRetriever(db=MagicMock())

        # 4. Reset the mock to test the call inside retrieve() in isolation
        mock_instance.encode.reset_mock()
        mock_instance.encode.return_value = np.random.rand(1, 384).astype('float32') # For the query

        # 5. Mock the BM25 scores to control the ranking logic
        retriever.bm25 = MagicMock()
        retriever.bm25.get_scores.return_value = np.array([0.1, 0.9])

        # 6. Call the method under test
        results = retriever.retrieve("test query")

        # --- Assert ---
        assert results is not None
        assert len(results) > 0
        # Check that encode was called exactly once within the retrieve method
        mock_instance.encode.assert_called_once_with("test query", convert_to_tensor=True)
        # With tied RRF scores, the result depends on stable sort order.
        # The dense retriever prefers 'Goal Specificity' (rank 1), and BM25 prefers 'Signature Missing' (rank 1).
        # This results in a tie, and the original order ([Goal, Signature]) is preserved.
        assert results[0]['name'] == 'Goal Specificity'