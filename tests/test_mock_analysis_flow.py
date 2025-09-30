import asyncio
import pytest
from httpx import AsyncClient

from src.api.main import app
from src.auth import get_current_active_user
from src import schemas

# Mark all tests in this file as asyncio tests
pytestmark = pytest.mark.asyncio


@pytest.fixture
def override_auth():
    """A fixture to override authentication for the duration of a test."""
    def _override_get_current_active_user():
        return dummy_user

    app.dependency_overrides[get_current_active_user] = _override_get_current_active_user
    yield
    # Clean up the override after the test is done
    app.dependency_overrides.pop(get_current_active_user, None)


async def test_full_mock_analysis_flow(
    async_client: AsyncClient, override_auth: None
):
    """
    Tests the full, end-to-end analysis flow using the mock service in an async context.
    This test confirms that a user can submit a document, poll for the status,
    and receive the complete mock analysis data.
    """
    # 1. Submit the document for analysis
    file_content = b"This is a test document for the async full flow."
    files = {"file": ("test_flow.txt", file_content, "text/plain")}
    data = {"discipline": "pt", "analysis_mode": "rubric"}

    response = await async_client.post("/analysis/analyze", files=files, data=data)
    assert response.status_code == 202, "Failed to submit document for analysis"
    response_data = response.json()
    task_id = response_data.get("task_id")
    assert task_id is not None, "API did not return a task_id"

    # 2. Poll the status endpoint until the task is complete
    result = None
    for _ in range(10):  # Poll up to 10 times
        response = await async_client.get(f"/analysis/status/{task_id}")
        assert response.status_code == 200, f"Failed to get status for task {task_id}"
        data = response.json()
        if data.get("status") == "completed":
            result = data
            break
        await asyncio.sleep(0.1)  # Use asyncio.sleep for non-blocking delay

    assert result is not None, "Task did not complete within the polling timeout"

    # 3. Verify the mock data in the result
    assert result["status"] == "completed"
    assert "result" in result
    mock_result = result["result"]

    # The mock analysis service returns a specific structure.
    assert "analysis" in mock_result
    analysis_data = mock_result["analysis"]
    assert analysis_data["compliance_score"] == 75.0
    assert "MOCK-001" in [f["rule_id"] for f in analysis_data["findings"]]
    assert "MOCK-002" in [f["rule_id"] for f in analysis_data["findings"]]