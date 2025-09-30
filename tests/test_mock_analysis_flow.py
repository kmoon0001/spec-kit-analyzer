import os
import sys
import time
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

# Ensure the src directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.api.main import app
from src.auth import get_current_active_user
from src.database import schemas
from src.config import get_settings


@pytest.fixture(scope="module")
def client():
    """Create a TestClient for the API with authentication and settings overridden."""

    def override_get_current_active_user():
        """Override dependency to return a dummy user."""
        return schemas.User(id=1, username="testuser", is_active=True, is_admin=False)

    app.dependency_overrides[get_current_active_user] = override_get_current_active_user

    # Clear the cache for get_settings to ensure our patch is effective
    get_settings.cache_clear()
    original_settings = get_settings()
    mock_settings = original_settings.copy(update={"use_ai_mocks": True})

    # We patch get_settings in the module where it is imported and used (the dependencies module)
    with patch("src.api.dependencies.get_settings", return_value=mock_settings):
        with TestClient(app) as c:
            yield c

    app.dependency_overrides.clear()


def test_full_mock_analysis_flow(client: TestClient):
    """
    Tests the full, end-to-end analysis flow using the mock service.
    This test confirms that a user can submit a document, poll for the status,
    and receive the complete mock analysis data.
    """
    # 1. Create a dummy file to upload
    dummy_filename = "test_document_for_flow.txt"
    with open(dummy_filename, "w") as f:
        f.write("This is a test document for the full flow.")

    task_id = None
    try:
        # 2. Submit the document for analysis
        with open(dummy_filename, "rb") as f:
            response = client.post(
                "/analysis/analyze",
                files={"file": (dummy_filename, f, "text/plain")},
                data={"discipline": "pt", "analysis_mode": "rubric"},
            )
        assert response.status_code == 202, "Failed to submit document for analysis"
        response_data = response.json()
        task_id = response_data.get("task_id")
        assert task_id is not None, "API did not return a task_id"

        # 3. Poll the status endpoint until the task is complete
        result = None
        for _ in range(10):  # Poll up to 10 times (e.g., 10 seconds)
            response = client.get(f"/analysis/status/{task_id}")
            assert response.status_code == 200, f"Failed to get status for task {task_id}"
            data = response.json()
            if data.get("status") == "completed":
                result = data
                break
            time.sleep(1)

        assert result is not None, "Task did not complete within the polling timeout"

        # 4. Verify the mock data in the result
        assert result["status"] == "completed"
        assert "result" in result
        mock_result = result["result"]
        assert "analysis" in mock_result
        analysis_data = mock_result["analysis"]
        assert analysis_data["compliance_score"] == 75.0
        assert "MOCK-001" in [f["rule_id"] for f in analysis_data["findings"]]
        assert "MOCK-002" in [f["rule_id"] for f in analysis_data["findings"]]
        print("\nEnd-to-end mock analysis flow verified successfully!")

    finally:
        # 5. Clean up the dummy file
        if os.path.exists(dummy_filename):
            os.remove(dummy_filename)