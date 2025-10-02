import os
import sys
import time
import datetime

import pytest
from fastapi.testclient import TestClient

# Ensure the src directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.api.main import app
from src.auth import get_current_active_user
from src.database import schemas


@pytest.fixture(scope="module")
def client_with_auth_override():
    """
    Provides a TestClient with the user authentication dependency overridden.
    This is scoped to the module to avoid polluting other test files.
    """
    dummy_user = schemas.User(
        id=1,
        username="testuser",
        is_active=True,
        is_admin=False,
        hashed_password="dummy_hash_for_mock_flow",
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )

    def override_get_current_active_user():
        return dummy_user

    app.dependency_overrides[get_current_active_user] = override_get_current_active_user

    with TestClient(app) as c:
        yield c

    # Clean up the override after the tests in this module are done
    app.dependency_overrides.clear()


def test_full_mock_analysis_flow(client_with_auth_override: TestClient):
    """
    Tests the full, end-to-end analysis flow using the mock service.
    This test confirms that a user can submit a document, poll for the status,
    and receive the complete mock analysis data.
    """
    client = client_with_auth_override
    dummy_filename = "test_document_for_flow.txt"
    with open(dummy_filename, "w") as f:
        f.write("This is a test document for the full flow.")

    task_id = None
    try:
        with open(dummy_filename, "rb") as f:
            # The endpoint is protected, so we need to pass a dummy token.
            # The actual content of the token doesn't matter because the dependency is overridden.
            headers = {"Authorization": "Bearer dummytoken"}
            response = client.post(
                "/analysis/analyze",
                files={"file": (dummy_filename, f, "text/plain")},
                data={"discipline": "pt", "analysis_mode": "rubric"},
                headers=headers,
            )
        assert (
            response.status_code == 202
        ), f"Failed to submit document for analysis: {response.text}"
        response_data = response.json()
        task_id = response_data.get("task_id")
        assert task_id is not None, "API did not return a task_id"

        result = None
        for _ in range(10):  # Poll up to 10 times
            response = client.get(f"/analysis/status/{task_id}", headers=headers)
            assert (
                response.status_code == 200
            ), f"Failed to get status for task {task_id}"
            data = response.json()
            if data.get("status") == "completed":
                result = data
                break
            time.sleep(1)

        assert result is not None, "Task did not complete within the polling timeout"
        assert result["status"] == "completed"
        assert "result" in result
        mock_result = result["result"]
        assert "analysis" in mock_result
        analysis_data = mock_result["analysis"]
        assert analysis_data["compliance_score"] == 75.0
        assert "MOCK-001" in [f["rule_id"] for f in analysis_data["findings"]]

    finally:
        if os.path.exists(dummy_filename):
            os.remove(dummy_filename)
