import pytest
import os
import sys
import logging
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.database import Base
from src.core.llm_service import LLMService
from src.core.nlg_service import NLGService
from src.core.ner import NERPipeline
from src.core.retriever import HybridRetriever
from src.core.compliance_analyzer import ComplianceAnalyzer
from src.core.fact_checker_service import FactCheckerService
from src.core.prompt_manager import PromptManager
from src.core.explanation import ExplanationEngine

def pytest_configure(config):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Mock Fixtures for AI Services ---

@pytest.fixture(scope="session")
def mock_llm_service():
    """Mocks the LLMService to avoid model loading."""
    service = MagicMock(spec=LLMService)
    service.generate_analysis.return_value = '{"findings": []}'
    return service

@pytest.fixture(scope="session")
def mock_ner_pipeline():
    """Mocks the NERPipeline."""
    service = MagicMock(spec=NERPipeline)
    service.extract_entities.return_value = []
    return service

@pytest.fixture(scope="session")
def mock_hybrid_retriever():
    """Mocks the HybridRetriever."""
    service = MagicMock(spec=HybridRetriever)
    service.retrieve.return_value = []
    return service

@pytest.fixture(scope="session")
def mock_nlg_service(mock_llm_service):
    """Mocks the NLGService."""
    # The NLGService now requires these arguments, so we provide mocks
    return NLGService(llm_service=mock_llm_service, prompt_template_path="")

@pytest.fixture(scope="session")
def mock_fact_checker_service():
    """Mocks the FactCheckerService."""
    service = MagicMock(spec=FactCheckerService)
    service.is_finding_plausible.return_value = True
    return service

# --- Database Fixtures for Isolated Testing ---

@pytest.fixture(scope="session")
def test_engine():
    """Creates an in-memory SQLite database engine for the test session."""
    return create_engine("sqlite:///:memory:")

@pytest.fixture(scope="session")
def setup_database(test_engine):
    """Sets up the database schema for the test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def db_session(test_engine, setup_database):
    """Provides a transactional database session for a single test function."""
    connection = test_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()

# --- Fixture for the main ComplianceAnalyzer ---

@pytest.fixture(scope="session")
def compliance_analyzer(
    mock_hybrid_retriever,
    mock_ner_pipeline,
    mock_llm_service,
    mock_nlg_service,
    mock_fact_checker_service,
):
    """Provides a fully mocked ComplianceAnalyzer instance."""
    return ComplianceAnalyzer(
        retriever=mock_hybrid_retriever,
        ner_pipeline=mock_ner_pipeline,
        llm_service=mock_llm_service,
        nlg_service=mock_nlg_service,
        explanation_engine=MagicMock(spec=ExplanationEngine),
        prompt_manager=MagicMock(spec=PromptManager),
        fact_checker_service=mock_fact_checker_service,
    )