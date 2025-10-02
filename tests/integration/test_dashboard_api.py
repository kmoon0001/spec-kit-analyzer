import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from src.api.main import app
from src.auth import get_current_active_user
from src.database import schemas
from src.config import get_settings


@pytest.mark.asyncio
async def test_get_director_dashboard_data_unauthorized(async_client):
    """
    Test that a non-admin user cannot access the director dashboard.
    """
    # Manually create a mock user for testing purposes
    mock_user = schemas.User(
        id=1,
        username="testuser",
        is_active=True,
        is_admin=False,
        created_at=datetime.now(timezone.utc),
    )
    try:
        app.dependency_overrides[get_current_active_user] = lambda: mock_user

        # For now, we'll manually create a token for the mock_user
        mock_token = "mock_access_token"
        headers = {"Authorization": f"Bearer {mock_token}"}

        response = await async_client.get(
            "/dashboard/director-dashboard", headers=headers
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_director_dashboard_data_as_admin(async_client, mocker):
    settings = get_settings()
    """
    Test that an admin user can successfully fetch director dashboard data.
    """
    # Manually create a mock user for testing purposes
    mock_user = schemas.User(
        id=1,
        username="testuser",
        is_active=True,
        is_admin=True,
        created_at=datetime.now(timezone.utc),
    )
    try:
        app.dependency_overrides[get_current_active_user] = lambda: mock_user

        # Mock the CRUD functions
        mock_crud = mocker.patch(
            "src.api.routers.dashboard.crud", new_callable=mocker.AsyncMock
        )
        mock_crud.get_total_findings_count.return_value = 10
        mock_crud.get_team_habit_summary.return_value = []
        mock_crud.get_clinician_habit_breakdown.return_value = []

        # For now, we'll manually create a token for the mock_user
        mock_token = "mock_access_token"
        headers = {"Authorization": f"Bearer {mock_token}"}

        response = await async_client.get(
            "/dashboard/director-dashboard", headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_findings"] == 10
        assert data["team_habit_summary"] == []
        assert data["clinician_habit_breakdown"] == []
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_generate_coaching_focus_as_admin(async_client, mocker):
    """
    Test that an admin can successfully generate an AI coaching focus.
    """
    settings = get_settings()
    # Manually create a mock user for testing purposes
    mock_user = schemas.User(
        id=1,
        username="testuser",
        is_active=True,
        is_admin=True,
        created_at=datetime.now(timezone.utc),
    )
    try:
        app.dependency_overrides[get_current_active_user] = lambda: mock_user

        mock_llm_service_instance = MagicMock()
        mock_llm_service_instance.is_ready.return_value = True
        mock_llm_service_instance.generate.return_value = '{"focus_title": "Test Focus", "summary": "Test Summary", "root_cause": "Test Cause", "action_steps": ["Step 1"]}'
        mock_llm_service_instance.parse_json_output.return_value = {
            "focus_title": "Test Focus",
            "summary": "Test Summary",
            "root_cause": "Test Cause",
            "action_steps": ["Step 1"],
        }
        mocker.patch(
            "src.api.routers.dashboard.LLMService",
            return_value=mock_llm_service_instance,
        )

        # Mock the CRUD functions
        mock_crud = mocker.patch(
            "src.api.routers.dashboard.crud", new_callable=mocker.AsyncMock
        )
        mock_crud.get_total_findings_count.return_value = 10
        mock_crud.get_team_habit_summary.return_value = []
        mock_crud.get_clinician_habit_breakdown.return_value = []
        dashboard_data = {
            "total_findings": 10,
            "team_habit_summary": [],
            "clinician_habit_breakdown": [],
        }

        # For now, we'll manually create a token for the mock_user
        mock_token = "mock_access_token"
        headers = {"Authorization": f"Bearer {mock_token}"}

        response = await async_client.post(
            "/dashboard/coaching-focus", json=dashboard_data, headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["focus_title"] == "Test Focus"
        assert data["summary"] == "Test Summary"
        assert data["action_steps"] == ["Step 1"]
    finally:
        app.dependency_overrides.clear()