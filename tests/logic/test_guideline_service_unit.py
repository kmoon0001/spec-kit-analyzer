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
        # Simulate a search result: (distances, indices)
        mock_index.search.return_value = (np.array([[0.1, 0.2]]), np.array([[0, 1]]))
        mock.IndexFlatL2.return_value = mock_index
        yield mock

# Now import the service after mocks are set up
from src.guideline_service import GuidelineService

@pytest.fixture
def guideline_service(mock_sentence_transformer, mock_faiss):
    service = GuidelineService(sources=[])
    service.guideline_chunks = [("sentence1 in section1", "Section 0"), ("sentence2 in section1", "Section 0")]
    service.faiss_index = MagicMock()
    service.faiss_index.search.return_value = (np.array([[0.1]]), np.array([[0]]))
    service.is_index_ready = True
    return service

def test_search_successful(guideline_service: GuidelineService):
    """
    Tests a successful hierarchical search call.
    """
    query = "test query"
    results = guideline_service.search(query)

    assert len(results) == 1
    assert results[0]['text'] == 'sentence1 in section1'
    assert results[0]['source'] == 'Section 0'


def test_search_with_no_index(guideline_service: GuidelineService):
    """
    Tests that search returns an empty list if the index is not ready.
    """
    guideline_service.is_index_ready = False
    results = guideline_service.search("another query")
    assert results == []
