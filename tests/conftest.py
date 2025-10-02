import logging
import os
import sys
from typing import Generator
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from src.database import models, crud, schemas
from src.api.main import app
from src.core.compliance_analyzer import ComplianceAnalyzer
from src.core.explanation import ExplanationEngine
from src.core.fact_checker_service import FactCheckerService
from src.core.hybrid_retriever import HybridRetriever
from src.core.llm_service import LLMService
from src.core.ner import NERPipeline
from src.core.nlg_service import NLGService
from src.core.prompt_manager import PromptManager
from src.database.database import Base, get_async_db

# Ensure the project root is in the Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def pytest_configure(config: pytest.Config) -> None:
    """Ensure a consistent logging format during test runs."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


# --- Mocked service fixtures -------------------------------------------------


@pytest.fixture(scope="session")
def mock_llm_service() -> MagicMock:
    """Provide a stubbed LLM service so no real model loads during tests."""
    service = MagicMock(spec=LLMService)
    service.generate_analysis.return_value = '{"findings": []}'
    service.parse_json_output.return_value = {"findings": []}
    service.is_ready.return_value = True
    return service


@pytest.fixture(scope="session")
def mock_ner_pipeline() -> MagicMock:
    """Stub the NER pipeline to avoid model downloads."""
    service = MagicMock(spec=NERPipeline)
    service.extract_entities.return_value = []
    return service


@pytest.fixture(scope="session")
def mock_hybrid_retriever() -> MagicMock:
    """Prevent HybridRetriever from touching FAISS, BM25, or the database."""
    service = MagicMock(spec=HybridRetriever)
    service.retrieve.return_value = []
    return service


@pytest.fixture(scope="session")
def mock_fact_checker_service() -> MagicMock:
    """Bypass expensive fact checking logic."""
    service = MagicMock(spec=FactCheckerService)
    service.is_finding_plausible.return_value = True
    return service


@pytest.fixture(scope="session")
def mock_prompt_manager() -> MagicMock:
    """Provide a prompt manager that never reads template files."""
    service = MagicMock(spec=PromptManager)
    service.build_prompt.return_value = ""
    return service


@pytest.fixture(scope="session")
def mock_explanation_engine() -> MagicMock:
    """Avoid running explanation generation logic."""
    service = MagicMock(spec=ExplanationEngine)
    service.add_explanations.side_effect = lambda findings, *_: findings
    return service


@pytest.fixture(scope="session")
def mock_nlg_service() -> MagicMock:
    service = MagicMock(spec=NLGService)
    service.generate_personalized_tip.return_value = "Tip"
    return service


# --- Synchronous Database fixtures -------------------------------------------


@pytest.fixture(scope="session")
def test_engine():
    """Create an in-memory SQLite engine for the entire test session."""
    return create_engine("sqlite:///:memory:")


@pytest.fixture(scope="session")
def setup_database(test_engine) -> Generator[None, None, None]:
    """Create all tables once per session and drop them afterwards."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(test_engine, setup_database) -> Generator[Session, None, None]:
    """Provide a transactional session that rolls back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session: Session = session_factory()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


# --- High-level analyzer fixture --------------------------------------------


@pytest.fixture(scope="session")
def compliance_analyzer(
    mock_hybrid_retriever: MagicMock,
    mock_ner_pipeline: MagicMock,
    mock_llm_service: MagicMock,
    mock_explanation_engine: MagicMock,
    mock_prompt_manager: MagicMock,
    mock_fact_checker_service: MagicMock,
    mock_nlg_service: MagicMock,
) -> ComplianceAnalyzer:
    """Assemble a ComplianceAnalyzer backed entirely by mocks."""
    return ComplianceAnalyzer(
        retriever=mock_hybrid_retriever,
        ner_pipeline=mock_ner_pipeline,
        llm_service=mock_llm_service,
        explanation_engine=mock_explanation_engine,
        prompt_manager=mock_prompt_manager,
        fact_checker_service=mock_fact_checker_service,
        nlg_service=mock_nlg_service,
    )


# --- Async Database and Test Client Fixtures ---------------------------------

# The URI format is important for shared in-memory DBs
ASYNC_SQLITE_URL = (
    "sqlite+aiosqlite:///file:memdb_async?mode=memory&cache=shared&uri=true"
)

async_engine = create_async_engine(
    ASYNC_SQLITE_URL, connect_args={"check_same_thread": False}
)


@pytest_asyncio.fixture(scope="session")
async def setup_async_database():
    """Create all tables for the async database once per session."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def test_db(
    setup_async_database: None,
) -> Generator[AsyncSession, None, None]:
    """
    Provide a transactional scope for each test.
    This ensures a clean database state for each test function.
    """
    connection = await async_engine.connect()
    transaction = await connection.begin()

    async_session_factory = async_sessionmaker(
        connection, class_=AsyncSession, expire_on_commit=False
    )
    session = async_session_factory()

    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def async_client(
    test_db: AsyncSession,
) -> Generator[AsyncClient, None, None]:
    """
    Provide an async test client that uses the same transactional session
    as the test function.
    """

    async def override_get_async_db_for_test() -> Generator[AsyncSession, None, None]:
        yield test_db

    app.dependency_overrides[get_async_db] = override_get_async_db_for_test

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.pop(get_async_db, None)


# --- Test User Data ---------------------------------------------------------

test_user_credentials = {"username": "testuser", "password": "test_password"}


@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession) -> models.User:
    """Create a standard user for testing purposes."""
    # Bypass actual password hashing for testing purposes
    # Use a mock hashed password that is valid in format but doesn't require bcrypt to generate
    mock_hashed_password = (
        "$2b$12$mockhashedpasswordstringforetesting12345678901234567890"
    )
    user_in = schemas.UserCreate(
        username=test_user_credentials["username"],
        password="mockpass",  # A short placeholder password for the schema
    )
    user = await crud.create_user(
        db=test_db, user=user_in, hashed_password=mock_hashed_password
    )
    return user
