import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.retriever import HybridRetriever
from src.models import Rubric

# Mark all tests in this file as async
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_settings():
    """Fixture for mock settings."""
    settings = MagicMock()
    settings.dense_model_name = "sentence-transformers/all-MiniLM-L6-v2"  # A real, but small model for testing
    settings.rrf_k = 60
    return settings

@pytest.fixture
def mock_db_session():
    """Fixture for a mock async database session."""
    return AsyncMock()

@pytest.fixture
def sample_rules():
    """Fixture for sample rubric data."""
    return [
        Rubric(id=1, name="Rule 1", content="This is about python coding.", category="tech"),
        Rubric(id=2, name="Rule 2", content="This is about data science.", category="tech"),
        Rubric(id=3, name="Rule 3", content="This is about patient care.", category="health"),
    ]

@patch('src.crud.get_rubrics')
async def test_initialization_and_data_loading(mock_get_rubrics, mock_settings, sample_rules):
    """
    Test that the HybridRetriever initializes correctly, loads rules from the DB,
    and builds its internal corpus and embeddings.
    """
    # Arrange
    mock_get_rubrics.return_value = sample_rules

    # Act
    with patch('src.config.get_settings', return_value=mock_settings):
        retriever = HybridRetriever(settings=mock_settings)
        await retriever.initialize()

    # Assert
    assert retriever._is_initialized
    assert len(retriever.rules) == len(sample_rules)
    assert len(retriever.corpus) == len(sample_rules)
    assert "python coding" in retriever.corpus[0]
    assert retriever.bm25 is not None
    assert retriever.dense_retriever is not None
    assert retriever.corpus_embeddings is not None
    assert retriever.corpus_embeddings.shape[0] == len(sample_rules)

@patch('src.crud.get_rubrics', new_callable=AsyncMock)
async def test_retrieval_flow(mock_get_rubrics, mock_settings, sample_rules):
    """
    Test the full, non-blocking retrieval flow.
    """
    # Arrange
    mock_get_rubrics.return_value = sample_rules
    query = "What are the best practices for python?"

    with patch('src.config.get_settings', return_value=mock_settings):
        retriever = HybridRetriever(settings=mock_settings)
        await retriever.initialize()

    # Act
    results = await retriever.retrieve(query, top_k=1)

    # Assert
    assert len(results) == 1
    assert results[0]['name'] == "Rule 1"
    assert "python coding" in results[0]['content']

@patch('src.crud.get_rubrics', new_callable=AsyncMock)
async def test_category_filtering(mock_get_rubrics, mock_settings, sample_rules):
    """
    Test that the retriever correctly filters results by category.
    """
    # Arrange
    mock_get_rubrics.return_value = sample_rules
    query = "What is important for health?"
    
    with patch('src.config.get_settings', return_value=mock_settings):
        retriever = HybridRetriever(settings=mock_settings)
        await retriever.initialize()

    # Act
    results = await retriever.retrieve(query, top_k=1, category_filter="health")

    # Assert
    assert len(results) == 1
    assert results[0]['name'] == "Rule 3"
    assert results[0]['category'] == "health"

@patch('src.crud.get_rubrics', new_callable=AsyncMock)
async def test_retriever_with_no_rules(mock_get_rubrics, mock_settings):
    """
    Test the retriever's behavior when the database returns no rules.
    """
    # Arrange
    mock_get_rubrics.return_value = []

    with patch('src.config.get_settings', return_value=mock_settings):
        retriever = HybridRetriever(settings=mock_settings)
        await retriever.initialize()

    # Act
    results = await retriever.retrieve("any query")

    # Assert
    assert retriever._is_initialized
    assert len(retriever.rules) == 0
    assert len(results) == 0

@patch('src.core.retriever.asyncio.to_thread')
@patch('src.crud.get_rubrics', new_callable=AsyncMock)
async def test_cpu_bound_work_is_offloaded(mock_get_rubrics, mock_to_thread, mock_settings, sample_rules):
    """
    Verify that the CPU-bound part of the retrieval is called via asyncio.to_thread.
    """
    # Arrange
    mock_get_rubrics.return_value = sample_rules
    # The thread returns a list of indices
    mock_to_thread.return_value = [0, 1, 2]
    
    with patch('src.config.get_settings', return_value=mock_settings):
        retriever = HybridRetriever(settings=mock_settings)
        await retriever.initialize()

    # Act
    await retriever.retrieve("some query")

    # Assert
    mock_to_thread.assert_called_once()