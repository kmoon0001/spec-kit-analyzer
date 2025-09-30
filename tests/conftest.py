import asyncio
import logging
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.api.dependencies import get_analysis_service
from src.api.main import app
from src.config import get_settings
from src.core.analysis_service import AnalysisService
from src.core.mock_analysis_service import MockAnalysisService
from src.database.database import Base, get_async_db

# --- Test Configuration ---

# Use a fast, in-memory SQLite database for testing.
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


def pytest_configure(config: pytest.Config) -> None:
    """Ensure a consistent logging format during test runs."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an instance of the default event loop for the entire test session.
    This is a standard pytest-asyncio fixture.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# --- Mocked Service Fixtures ---


@pytest.fixture(scope="session")
def mock_analysis_service() -> MockAnalysisService:
    """Provide a mocked analysis service to avoid real model loading."""
    return MockAnalysisService()


# --- Database Fixtures (Async) ---


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create an async engine for the test session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    # Create all tables once per session.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    # The engine is disposed of in the async_client fixture's finalizer.


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a transactional async database session that rolls back after each test.
    """
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        await session.begin_nested()
        yield session
        await session.rollback()


# --- API Testing Fixtures ---


@pytest_asyncio.fixture(scope="session")
async def async_client(
    mock_analysis_service: MockAnalysisService,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a fully-featured async test client for the FastAPI application.
    This client runs against a test instance of the app with mocked services
    and an in-memory database.
    """
    # Override dependencies for the test environment.
    app.dependency_overrides[get_analysis_service] = lambda: mock_analysis_service

    # Use an in-memory async database for tests.
    test_engine = create_async_engine(TEST_DATABASE_URL)
    TestingSessionLocal = async_sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_async_db] = override_get_db

    # Initialize the database tables.
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from httpx import ASGITransport

    # Run the application within the async test client.
    # The 'app' argument is passed to the transport, not the client directly.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Clean up: drop all tables after tests are done.
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Dispose of the engine to close all connections.
    await test_engine.dispose()