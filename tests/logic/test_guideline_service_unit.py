import pytest
from unittest.mock import MagicMock, patch
import numpy as np

# Mock the config before importing the service
@pytest.fixture(autouse=True)
def mock_settings():
    with patch('src.utils.load_config') as mock_load_config:
        mock_load_config.return_value = {
            'models': {
                'retriever': 'mock-retriever-model'
            },
            'retrieval_settings': {
                'similarity_top_k': 2
            }
        }
        yield

# Mock the heavy dependencies
@pytest.fixture
def mock_sentence_transformer():
    with patch('src.guideline_service.SentenceTransformer') as mock:
        mock_instance = MagicMock()

        # Simulate the return of a mock tensor that has a .cpu().numpy() chain
        mock_tensor = MagicMock()
        mock_tensor.cpu.return_value.numpy.return_value = np.array([[0.1, 0.2, 0.3]], dtype=np.float32)
        mock_instance.encode.return_value = mock_tensor

        mock.return_value = mock_instance
        yield mock

@pytest.fixture
def mock_faiss():
    with patch('src.guideline_service.faiss') as mock:
        mock_index = MagicMock()
        # Simulate a search result: (distances, indices) with distances above the threshold
        mock_index.search.return_value = (np.array([[0.9, 0.8]]), np.array([[0, 1]]))
        mock.IndexFlatIP.return_value = mock_index
        yield mock

# Now import the service after mocks are set up
from src.guideline_service import GuidelineService

@pytest.fixture
def guideline_service(mock_sentence_transformer, mock_faiss):
    # We need to prevent __init__ from running its own logic now that we mock things
    with patch.object(GuidelineService, '_load_or_build_index', return_value=None):
        service = GuidelineService(sources=["dummy_source.txt"])
        # Manually set the necessary attributes for testing the search method
        service.is_index_ready = True
        service.faiss_index = mock_faiss.IndexFlatIP()
        service.guideline_chunks = [("chunk1 text", "source1"), ("chunk2 text", "source2")]
        return service

def test_search_successful(guideline_service: GuidelineService):
    """
    Tests a successful search call.
    """
    query = "test query"
    results = guideline_service.search(query)

    # Assertions
    assert len(results) == 2
    assert results[0]['text'] == "chunk1 text"
    assert results[1]['source'] == "source2"

    # Check that the underlying model and index were called correctly
    guideline_service.model.encode.assert_called_once_with([query], convert_to_tensor=True)
    guideline_service.faiss_index.search.assert_called_once()


def test_search_with_no_index(guideline_service: GuidelineService):
    """
    Tests that search returns an empty list if the index is not ready.
    """
    guideline_service.is_index_ready = False
    results = guideline_service.search("another query")
    assert results == []
