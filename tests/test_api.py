import os
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.database import Base, get_async_db
from src.auth import get_current_active_user
from src.database import models
from src.api.dependencies import get_analysis_service

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_api.db"

engine = create_async_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    if os.path.exists("test_api.db"):
        os.remove("test_api.db")


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    async def override_get_async_db() -> AsyncSession:
        yield db_session

    async def override_get_current_active_user() -> models.User:
        return models.User(
            id=1,
            username="testuser",
            hashed_password="hashed",
            is_active=True,
            is_admin=False,
        )

    app.dependency_overrides[get_async_db] = override_get_async_db
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    app.dependency_overrides[get_analysis_service] = lambda: MagicMock()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_read_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the Clinical Compliance Analyzer API"
    }


@pytest.mark.asyncio
@patch("src.api.routers.analysis.run_analysis_and_save")
async def test_analyze_document_endpoint(mock_run_analysis, client: AsyncClient):
    file_content = b"This is a test document."
    response = await client.post(
        "/analysis/analyze", files={"file": ("test.txt", file_content, "text/plain")}
    )
    assert response.status_code == 202
    response_json = response.json()
    assert "task_id" in response_json
    assert response_json["status"] == "processing"
    assert mock_run_analysis.called


@pytest.mark.asyncio
async def test_get_dashboard_reports_endpoint_empty(client: AsyncClient):
    response = await client.get("/dashboard/reports")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json() == []
