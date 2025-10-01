import pytest

from datetime import datetime

from src.api.main import app
from src.auth import get_current_active_user
from src import schemas



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
        hashed_password="$2b$12$mockhashedpasswordstringforetesting12345678901234567890",
        created_at=datetime.utcnow(),
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
    """
    Test that an admin user can successfully fetch director dashboard data.
    """
    mock_user = schemas.User(
        id=1,
        username="testuser",
        is_active=True,
        is_admin=True,
        hashed_password="$2b$12$mockhashedpasswordstringforetesting12345678901234567890",
        created_at=datetime.utcnow(),
    )
    try:
        app.dependency_overrides[get_current_active_user] = lambda: mock_user

        mock_crud = mocker.patch(
            "src.api.routers.dashboard.crud", new_callable=mocker.AsyncMock
        )
        mock_crud.get_total_findings_count.return_value = 150
        mock_crud.get_team_habit_summary.return_value = [
            {"habit_name": "Habit 1", "count": 50}
        ]
        mock_crud.get_clinician_habit_breakdown.return_value = [
            {"clinician_name": "Dr. Doe", "habit_name": "Habit 1", "count": 25}
        ]

        # For now, we'll manually create a token for the mock_user
        mock_token = "mock_access_token"
        headers = {"Authorization": f"Bearer {mock_token}"}

        response = await async_client.get(
            "/dashboard/director-dashboard", headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_findings"] == 150
        assert data["team_habit_summary"][0]["habit_name"] == "Habit 1"
        assert data["clinician_habit_breakdown"][0]["clinician_name"] == "Dr. Doe"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_generate_coaching_focus_as_admin(async_client, mocker):
    """
    Test that an admin can successfully generate an AI coaching focus.
    """
