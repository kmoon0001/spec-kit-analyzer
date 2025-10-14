from dataclasses import dataclass
from pathlib import Path

import pytest

from src.mock_api import create_mock_test_client


@dataclass
class DummyUser:
    id: int
    username: str
    is_active: bool = True
    is_admin: bool = False


@pytest.fixture(scope="module")
def mock_client():
    """Provide an authenticated client for the offline mock API."""

    dummy_user = DummyUser(id=7, username="test-user")

    with create_mock_test_client(dummy_user) as client:
        yield client


def test_full_mock_analysis_flow(mock_client) -> None:
    """Exercise the full mock analysis pipeline using the lightweight mock API."""

    client = mock_client
    dummy_filename = Path("test_document_for_flow.txt")
    dummy_filename.write_text("This is a test document for the full flow.", encoding="utf-8")

    headers = {"Authorization": "Bearer dummytoken"}
    with dummy_filename.open("rb") as file_handle:
        response = client.post(
            "/analysis/analyze",
            files={"file": (dummy_filename.name, file_handle, "text/plain")},
            data={"discipline": "pt", "analysis_mode": "rubric"},
            headers=headers,
        )

    dummy_filename.unlink(missing_ok=True)

    assert response.status_code == 202, f"Failed to submit document for analysis: {response.text}"
    response_data = response.json()
    task_id = response_data.get("task_id")
    assert task_id, "API did not return a task_id"

    status_response = client.get(f"/analysis/status/{task_id}", headers=headers)
    assert status_response.status_code == 200, f"Failed to get status for task {task_id}"

    task_payload = status_response.json()
    assert task_payload["status"] == "completed"
    assert "result" in task_payload

    mock_result = task_payload["result"]
    assert "analysis" in mock_result

    analysis_data = mock_result["analysis"]
    assert analysis_data["compliance_score"] == 75.0
    assert any(finding["rule_id"] == "MOCK-001" for finding in analysis_data.get("findings", []))
