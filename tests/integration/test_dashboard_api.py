import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock

# This is a placeholder for the actual FastAPI app instance
# In a real test setup, you would import the app from your project
from src.api.main import app


from src.database.models import User

@pytest.mark.asyncio
async def test_get_director_dashboard_data_unauthorized(async_client, test_user: User):
    """
    Test that a non-admin user cannot access the director dashboard.
    """
    # The test_user fixture creates a non-admin user by default.
    # The require_admin dependency should reject this request.
    # We need to get a token for the user first.
    response = await async_client.post(
        "/auth/token",
        data={"username": test_user.username, "password": "test"},
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.get("/dashboard/director-dashboard", headers=headers)
    assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_get_director_dashboard_data_as_admin(
    async_client, test_user: User, mocker
):
    """
    Test that an admin user can successfully fetch director dashboard data.
    """
    # Make the test user an admin for this test
    test_user.is_admin = True

    # Patch the setting directly in the module where it's used
    mocker.patch("src.api.routers.dashboard.settings.enable_director_dashboard", True)

    mock_crud = mocker.patch("src.api.routers.dashboard.crud")
    mock_crud.get_total_findings_count = AsyncMock(return_value=150)
    mock_crud.get_team_habit_summary = AsyncMock(
        return_value=[{"habit_name": "Habit 1", "count": 50}]
    )
    mock_crud.get_clinician_habit_breakdown = AsyncMock(
        return_value=[
            {"clinician_name": "Dr. Doe", "habit_name": "Habit 1", "count": 25}
        ]
    )

    # Get token for the admin user
    response = await async_client.post(
        "/auth/token",
        data={"username": test_user.username, "password": "test"},
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.get(
        "/dashboard/director-dashboard", headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_findings"] == 150
    assert data["team_habit_summary"][0]["habit_name"] == "Habit 1"
    assert data["clinician_habit_breakdown"][0]["clinician_name"] == "Dr. Doe"


@pytest.mark.asyncio
async def test_generate_coaching_focus_as_admin(
    async_client, test_user: User, mocker
):
    """
    Test that an admin can successfully generate an AI coaching focus.
    """
    test_user.is_admin = True
    mocker.patch("src.api.routers.dashboard.settings.enable_director_dashboard", True)

    mock_llm_service_instance = MagicMock()
    mock_llm_service_instance.is_ready.return_value = True
    mock_llm_service_instance.generate_analysis = AsyncMock(
            return_value='{"focus_title": "Test Focus", "summary": "Test Summary", "root_cause": "Test Cause", "action_steps": ["Step 1"]}'
    )
    mock_llm_service_instance.parse_json_output.return_value = {
        "focus_title": "Test Focus",
        "summary": "Test Summary",
            "root_cause": "Test Cause",
        "action_steps": ["Step 1"],
    }

    mocker.patch(
        "src.api.routers.dashboard.LLMService", return_value=mock_llm_service_instance
    )

    dashboard_data = {
        "total_findings": 10,
        "team_habit_summary": [],
        "clinician_habit_breakdown": [],
    }

    response = await async_client.post(
        "/auth/token",
        data={"username": test_user.username, "password": "test"},
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.post(
        "/dashboard/coaching-focus", json=dashboard_data, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["focus_title"] == "Test Focus"
    assert data["summary"] == "Test Summary"
    assert data["action_steps"] == ["Step 1"]