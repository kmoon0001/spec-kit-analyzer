import pytest
import pytest_asyncio
import logging
import os
import sys
from unittest.mock import MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import Base
from src.core.llm_service import LLMService
from src.core.ner import NERPipeline
from src.core.retriever import HybridRetriever
from src.core.compliance_analyzer import ComplianceAnalyzer
from src.core.fact_checker_service import FactCheckerService
from src.core.prompt_manager import PromptManager
from src.core.explanation import ExplanationEngine

def pytest_configure(config):
    """Configure logging for the test suite."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Mock Fixtures for AI Services ---

@pytest.fixture(scope="session")
def mock_llm_service():
    service = MagicMock(spec=LLMService)
    service.generate_text.return_value = '{"findings": []}'
    return service

@pytest.fixture(scope="session")
def mock_ner_pipeline():
    service = MagicMock(spec=NERPipeline)
    service.extract_entities.return_value = []
    return service

@pytest.fixture(scope="session")
def mock_hybrid_retriever():
    service = MagicMock(spec=HybridRetriever)
    service.retrieve_rules.return_value = []
    return service

@pytest.fixture(scope="session")
def mock_fact_checker_service():
    service = MagicMock(spec=FactCheckerService)
    service.is_finding_plausible.return_value = True
    return service

# --- Async Database Fixtures ---

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Creates an in-memory async SQLite database engine for the test session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine):
    """Provides a transactional async database session for a single test function."""
    async_session_factory = sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session

# --- Fixture for the main ComplianceAnalyzer ---

@pytest.fixture(scope="function")
def compliance_analyzer(
    mock_hybrid_retriever,
    mock_ner_pipeline,
    mock_llm_service,
    mock_fact_checker_service,
):
    """Provides a fully mocked ComplianceAnalyzer instance for unit testing."""
    return ComplianceAnalyzer(
        retriever=mock_hybrid_retriever,
        ner_pipeline=mock_ner_pipeline,
        llm_service=mock_llm_service,
        explanation_engine=MagicMock(spec=ExplanationEngine),
        prompt_manager=MagicMock(spec=PromptManager),
        fact_checker_service=mock_fact_checker_service,
    )
