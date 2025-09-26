import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import io
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.core.analysis_service import AnalysisService
from src.auth import get_current_active_user
from src.database import Base, get_db

# --- Test Database Setup ---

# Use a file-based SQLite database for tests to ensure consistency across anyio backends
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def setup_database():
    """Fixture to create and tear down the test database."""
    # Create the tables in the test database
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up the database file after the test module finishes
    os.remove("test.db")


def override_get_db():
    """Dependency override to use the test database."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# --- Mocks & Overrides ---

@pytest.fixture
def mock_analysis_service():
    return MagicMock(spec=AnalysisService)

@pytest.fixture
def mock_user():
    return MagicMock()

@pytest.fixture(autouse=True)
def override_dependencies(mock_analysis_service, mock_user, setup_database):
    """Overrides dependencies for all tests in this module."""
    app.dependency_overrides[AnalysisService] = lambda: mock_analysis_service
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()

# --- Test Client ---

@pytest.fixture
def client():
    """Provides a test client for the FastAPI app."""
    with patch('src.api.routers.analysis.BackgroundTasks'), TestClient(app) as c:
        yield c

# --- API Tests ---

@pytest.mark.anyio
async def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Clinical Compliance Analyzer API"}

@pytest.mark.anyio
async def test_analyze_document_endpoint(client: TestClient):
    file_content = b"This is a test document."
    file_bytes = io.BytesIO(file_content)
    response = client.post("/analysis/analyze", files={"file": ("test.txt", file_bytes, "text/plain")})
    assert response.status_code == 202
    response_json = response.json()
    assert "task_id" in response_json
    assert response_json["status"] == "processing"

@pytest.mark.anyio
async def test_get_dashboard_reports_endpoint(client: TestClient):
    """This test should now pass as the database and tables are correctly set up."""
    response = client.get("/dashboard/reports")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json() == []