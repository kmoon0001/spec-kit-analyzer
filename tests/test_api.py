import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import io

# Import the main app and override dependencies
from src.api.main import app
from src.core.analysis_service import AnalysisService
from src.auth import get_current_active_user

# --- Mocking Dependencies ---


@pytest.fixture
def mock_analysis_service():
    """Fixture to provide a mock of the main AnalysisService."""
    return MagicMock()


@pytest.fixture
def mock_user():
    """Fixture to provide a mock user object."""
    return MagicMock()


# This is the core of the test setup. We override the real dependencies with our mocks.
# This ensures no real AI models are loaded and no real auth logic is run.
app.dependency_overrides[AnalysisService] = mock_analysis_service
app.dependency_overrides[get_current_active_user] = mock_user

# --- Test Client ---


@pytest.fixture
def client():
    """Provides a test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c


# --- API Tests ---


def test_read_root(client: TestClient):
    """Tests the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the Clinical Compliance Analyzer API"
    }


def test_analyze_document_endpoint(
    client: TestClient, mock_analysis_service: MagicMock
):
    """Tests the main document analysis endpoint."""
    # Arrange: Mock the service to return a specific task ID
    mock_analysis_service.return_value.start_analysis.return_value = "test-task-id"

    # Simulate a file upload
    file_content = b"This is a test document."
    file_bytes = io.BytesIO(file_content)

    # Act
    response = client.post(
        "/analysis/analyze", files={"file": ("test.txt", file_bytes, "text/plain")}
    )

    # Assert
    assert response.status_code == 202  # Accepted
    assert response.json() == {"task_id": "test-task-id", "status": "processing"}


def test_get_dashboard_reports_endpoint(client: TestClient):
    """Tests the endpoint for fetching dashboard reports."""
    # This endpoint depends on the database via crud functions.
    # A full integration test would use a test database.
    # For this unit-style test, we assume the underlying crud function works
    # and the endpoint correctly returns what it receives.
    # We can mock the crud function if needed for a pure unit test.

    # For now, we just test that the endpoint exists and requires auth (which is mocked).
    response = client.get("/dashboard/reports")
    assert response.status_code == 200  # It will succeed because auth is mocked
    # In a real test with a test DB, we would assert the content:
    # assert isinstance(response.json(), list)


# Cleanup dependency overrides after tests are done
@pytest.fixture(autouse=True, scope="session")
def cleanup_overrides():
    yield
    app.dependency_overrides = {}
