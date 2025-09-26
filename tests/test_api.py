import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

from src.api.main import app
from src.database import Base, get_async_db
from src.auth import get_current_active_user
from src import models

# --- Async Test Database Setup ---
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_api.db"

engine = create_async_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# --- Fixtures ---

@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_database():
    """Fixture to create and tear down the test database for the module."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    os.remove("test_api.db")

@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Provides a clean database session for each test."""
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    """Provides an async test client with dependencies overridden."""
    
    async def override_get_async_db() -> AsyncSession:
        yield db_session

    async def override_get_current_active_user() -> models.User:
        # Mocks an active, authenticated user
        return models.User(id=1, username="testuser", email="test@test.com", is_active=True)

    app.dependency_overrides[get_async_db] = override_get_async_db
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user

    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()

# --- API Tests ---

@pytest.mark.asyncio
async def test_read_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Clinical Compliance Analyzer API"}

@pytest.mark.asyncio
@patch('src.api.routers.analysis.run_analysis_and_save') # Mock the background task
async def test_analyze_document_endpoint(mock_run_analysis, client: AsyncClient):
    file_content = b"This is a test document."
    response = await client.post(
        "/analysis/analyze", 
        files={"file": ("test.txt", file_content, "text/plain")}
    )
    assert response.status_code == 202
    response_json = response.json()
    assert "task_id" in response_json
    assert response_json["status"] == "processing"
    # Assert that the background task was called
    assert mock_run_analysis.called

@pytest.mark.asyncio
async def test_get_dashboard_reports_endpoint_empty(client: AsyncClient):
    """Tests the dashboard reports endpoint when no reports exist."""
    response = await client.get("/dashboard/reports")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json() == []
