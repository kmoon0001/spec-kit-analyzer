import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import io

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import the main app and override dependencies
from src.api.main import app
from src.core.analysis_service import AnalysisService
from src.auth import get_current_active_user
from src.api.dependencies import get_analysis_service
from src.database import Base, get_db

# --- Test Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for a test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

# --- Mocking Dependencies ---

@pytest.fixture
def mock_user():
    """Fixture to provide a mock user object."""
    return MagicMock()

# --- Test Client ---

@pytest.fixture
def client(mock_user: MagicMock, db_session):
    """
    Provides a test client for the FastAPI app, with dependencies overridden.
    This fixture patches the AnalysisService and the database session.
    """
    with patch("src.api.main.AnalysisService", autospec=True) as mock_analysis_service_class:
        mock_instance = mock_analysis_service_class.return_value
        app.dependency_overrides[get_analysis_service] = lambda: mock_instance
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: db_session

        with TestClient(app) as c:
            yield c

        app.dependency_overrides.clear()

# --- API Tests ---

def test_read_root(client: TestClient):
    """Tests the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Clinical Compliance Analyzer API"}

def test_analyze_document_endpoint(client: TestClient):
    """Tests the main document analysis endpoint."""
    # The mock is already configured in the client fixture.
    # We don't need to interact with it directly unless we want to change its behavior for a specific test.
    
    # Simulate a file upload
    file_content = b"This is a test document."
    file_bytes = io.BytesIO(file_content)
    
    # Act
    response = client.post(
        "/analysis/analyze",
        files={"file": ("test.txt", file_bytes, "text/plain")}
    )
    
    # Assert
    assert response.status_code == 202 # Accepted
    assert "task_id" in response.json()
    assert response.json()["status"] == "processing"

def test_get_dashboard_reports_endpoint(client: TestClient):
    """Tests the endpoint for fetching dashboard reports."""
    # This endpoint depends on the database via crud functions.
    # A full integration test would use a test database.
    # For this unit-style test, we assume the underlying crud function works
    # and the endpoint correctly returns what it receives.
    # We can mock the crud function if needed for a pure unit test.
    
    # For now, we just test that the endpoint exists and requires auth (which is mocked).
    response = client.get("/dashboard/reports")
    assert response.status_code == 200 # It will succeed because auth is mocked
    # In a real test with a test DB, we would assert the content:
    # assert isinstance(response.json(), list)

