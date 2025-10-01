import pytest
from datetime import datetime

from src.api.main import app
from src.auth import get_current_active_user
from src import schemas



@pytest.mark.asyncio
async def test_get_director_dashboard_with_filters(async_client, mocker):
    """
    Test that the director dashboard endpoint correctly handles date and discipline filters.
    """

    # Manually create a mock user for testing purposes
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

        # Make the request with filters
        params = {
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",
            "discipline": "PT",
        }
        response = await async_client.get(
            "/dashboard/director-dashboard", headers=headers, params=params
        )

        # Assertions
        assert response.status_code == 200

        # Verify that the CRUD functions were called with the correct filter arguments
        mock_crud.get_total_findings_count.assert_awaited_once()
        call_kwargs = mock_crud.get_total_findings_count.call_args.kwargs
        assert call_kwargs["discipline"] == "PT"
        assert str(call_kwargs["start_date"]) == "2023-01-01"
        assert str(call_kwargs["end_date"]) == "2023-01-31"

        mock_crud.get_team_habit_summary.assert_awaited_once()
        call_kwargs = mock_crud.get_team_habit_summary.call_args.kwargs
        assert call_kwargs["discipline"] == "PT"

        mock_crud.get_clinician_habit_breakdown.assert_awaited_once()
        call_kwargs = mock_crud.get_clinician_habit_breakdown.call_args.kwargs
        assert call_kwargs["discipline"] == "PT"
    finally:
        app.dependency_overrides = {}
