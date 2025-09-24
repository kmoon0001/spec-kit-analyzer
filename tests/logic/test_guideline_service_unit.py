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
    with patch.object(GuidelineService, '_load_or_build_index', return_value=None):
        service = GuidelineService(sources=["dummy_source.txt"])
        service.is_index_ready = True

        # Mock hierarchical data
        summary_index_mock = MagicMock()
        summary_index_mock.search.return_value = (np.array([[0.1]]), np.array([[0]]))
        service.summary_index = summary_index_mock

        service.sections_data = [{
            'id': 0,
            'summary': 'summary1',
            'sentences': ['sentence1 in section1', 'sentence2 in section1'],
            'source': 'Section 0'
        }]

        final_index_mock = MagicMock()
        final_index_mock.search.return_value = (np.array([[0.1]]), np.array([[0]]))
        mock_faiss.IndexFlatL2.return_value = final_index_mock

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

    guideline_service.model.encode.assert_called_with(['sentence1 in section1', 'sentence2 in section1'])
    guideline_service.summary_index.search.assert_called_once()


def test_search_with_no_index(guideline_service: GuidelineService):
    """
    Tests that search returns an empty list if the index is not ready.
    """
    guideline_service.is_index_ready = False
    results = guideline_service.search("another query")
    assert results == []
