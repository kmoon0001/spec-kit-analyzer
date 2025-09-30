import pytest
from unittest.mock import patch, ANY
from httpx import AsyncClient

from src.api.main import app
from src.auth import get_current_active_user
from src.database import schemas

# Mark all tests in this file as asyncio tests
pytestmark = pytest.mark.asyncio


@pytest.fixture
def override_auth():
    """A fixture to override authentication for the duration of a test."""
    dummy_user = schemas.User(id=1, username="testuser", is_active=True, is_admin=False)

    def _override_get_current_active_user():
        return dummy_user

    app.dependency_overrides[get_current_active_user] = _override_get_current_active_user
    yield
    # Clean up the override after the test is done
    app.dependency_overrides.pop(get_current_active_user, None)


async def test_analyze_document_api_route(
    async_client: AsyncClient, override_auth: None
):
    """
    Tests the POST /analysis/analyze API endpoint in a proper async manner.

    This test verifies the API logic, file handling, and background task creation
    using the new async test client and fixture system.
    """
    # Mock the background task function to check if it's called correctly.
    # The `mocker` fixture is provided by pytest-mock.
    with patch("src.api.routers.analysis.run_analysis_and_save") as mock_run_analysis:
        file_content = b"This is a test document for the async client."
        files = {"file": ("test_note_async.txt", file_content, "text/plain")}
        data = {"discipline": "pt", "analysis_mode": "rubric"}

        response = await async_client.post("/analysis/analyze", files=files, data=data)

        assert response.status_code == 202
        response_data = response.json()
        assert "task_id" in response_data
        assert response_data["status"] == "processing"

        # Verify that the background task was called once with the correct arguments.
        # We use ANY for values that are generated at runtime (e.g., file paths, services).
        mock_run_analysis.assert_called_once_with(
            ANY,  # The temporary file path
            response_data["task_id"],
            "test_note_async.txt",
            "pt",
            "rubric",
            ANY,  # The analysis_service instance
        )