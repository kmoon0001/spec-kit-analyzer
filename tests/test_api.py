import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import io

from src.api.main import app
from src.api.dependencies import get_analysis_service
from src.database import get_db

# --- Test Fixtures ---

@pytest.fixture(scope="function")
def client(compliance_analyzer, db_session):
    """
    Provides a test client with mocked dependencies for the API tests.
    This fixture ensures that all API calls are made against a mocked backend
    and an in-memory test database.
    """
    # Override the get_analysis_service dependency to return our mock analyzer
    app.dependency_overrides[get_analysis_service] = lambda: compliance_analyzer
    # Override the get_db dependency to use the in-memory test database session
    app.dependency_overrides[get_db] = lambda: db_session

    with TestClient(app) as c:
        yield c

    # Clean up the overrides after the tests in this module are done
    app.dependency_overrides = {}

# --- API Tests ---

def test_health_check(client: TestClient):
    """Tests the health check endpoint, which should succeed with a valid DB session."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}

def test_read_root(client: TestClient):
    """Tests the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Clinical Compliance Analyzer API"}

def test_analyze_document_endpoint(client: TestClient, compliance_analyzer: MagicMock):
    """
    Tests the main document analysis endpoint.
    This test verifies that the endpoint correctly receives a file, starts a background
    task, and returns the appropriate task ID.
    """
    # Mock the background task function to prevent it from actually running
    compliance_analyzer.get_document_embedding.return_value = b"mock_embedding"
    
    # Simulate a file upload
    file_content = b"This is a test document."
    file_bytes = io.BytesIO(file_content)
    
    # Act
    response = client.post(
        "/analysis/analyze", 
        files={"file": ("test.txt", file_bytes, "text/plain")},
        data={"discipline": "PT", "analysis_mode": "rubric"}
    )
    
    # Assert
    assert response.status_code == 202  # Accepted
    json_response = response.json()
    assert "task_id" in json_response
    assert json_response["status"] == "processing"