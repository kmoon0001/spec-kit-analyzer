import pytest
from unittest.mock import patch, MagicMock
import numpy as np

# Import the service *after* the mocks will be set up
from src.guideline_service import GuidelineService

@pytest.fixture
def mock_heavy_dependencies():
    """Mocks the heavy SentenceTransformer and FAISS dependencies."""
    with patch('src.guideline_service.SentenceTransformer') as mock_st_class, \
         patch('src.guideline_service.faiss') as mock_faiss_module:
        
        mock_st_instance = MagicMock()
        mock_st_instance.encode.return_value = np.random.rand(1, 384).astype('float32')
        mock_st_class.return_value = mock_st_instance

        mock_faiss_index = MagicMock()
        mock_faiss_index.search.return_value = (np.array([[0.1]]), np.array([[0]]))
        mock_faiss_module.IndexFlatL2.return_value = mock_faiss_index

        yield {
            "st_class": mock_st_class,
            "faiss_module": mock_faiss_module
        }

@pytest.fixture
def guideline_service(mock_heavy_dependencies):
    """Provides a GuidelineService instance for testing with mocked dependencies."""
    with patch.object(GuidelineService, '_load_or_build_index', return_value=None):
        service = GuidelineService(sources=["dummy_source.txt"])

    # Manually set the state that _load_or_build_index would have set
    service.is_index_ready = True
    service.guideline_chunks = [
        ('Test sentence 1 about Medicare.', 'dummy_source.txt'),
        ('This is another sentence.', 'dummy_source.txt'),
    ]
    # The model instance is already mocked via the class mock
    # Set the faiss_index to the mocked instance
    service.faiss_index = mock_heavy_dependencies["faiss_module"].IndexFlatL2()
    return service

<<<<<<< HEAD
def test_search_successful_orchestration(guideline_service: GuidelineService):
    """
    Tests that the search method correctly orchestrates the search.
    """
||||||| 4db3b6b
def test_search_successful_orchestration(guideline_service: 'GuidelineService'):
    """
    Tests that the search method correctly orchestrates the search process.
    """
=======
def test_search_successful_orchestration(guideline_service: 'GuidelineService'):
    """Tests that the search method correctly orchestrates the search process."""
>>>>>>> origin/main
    # Arrange
    query = "test query"

    # Act
    results = guideline_service.search(query)

    # Assert
    # 1. Check that the query was encoded
    guideline_service.model.encode.assert_called_with([query], convert_to_tensor=True)

    # 2. Check that the main index search was performed
    guideline_service.faiss_index.search.assert_called_once()

    # 3. Check that the results are correctly formatted
    assert len(results) > 0
    # The mock search returns index 0, so we expect the first chunk
    assert "Test sentence 1 about Medicare." in results[0]['text']
    assert results[0]['source'] == 'dummy_source.txt'

<<<<<<< HEAD
def test_search_returns_empty_if_index_not_ready(guideline_service: GuidelineService):
    """
    Tests that search returns an empty list if the index is not ready.
    """
||||||| 4db3b6b
def test_search_returns_empty_if_index_not_ready(guideline_service: 'GuidelineService'):
    """
    Tests that search returns an empty list if the index is not ready.
    """
=======
def test_search_returns_empty_if_index_not_ready(guideline_service: 'GuidelineService'):
    """Tests that search returns an empty list if the index is not ready."""
>>>>>>> origin/main
    # Arrange
    guideline_service.is_index_ready = False
    
    # Act
    results = guideline_service.search("another query")
    
    # Assert
    assert results == []
