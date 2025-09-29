import pytest
from unittest.mock import AsyncMock

from src.database.models import User

@pytest.mark.asyncio
async def test_get_director_dashboard_with_filters(
    async_client, test_user: User, mocker
):
    """
    Test that the director dashboard endpoint correctly handles date and discipline filters.
    """
    test_user.is_admin = True
    mocker.patch("src.api.routers.dashboard.settings.enable_director_dashboard", True)

    # Mock the CRUD functions
    mock_crud = mocker.patch("src.api.routers.dashboard.crud")
    mock_crud.get_total_findings_count = AsyncMock(return_value=10)
    mock_crud.get_team_habit_summary = AsyncMock(return_value=[])
    mock_crud.get_clinician_habit_breakdown = AsyncMock(return_value=[])

    # Get auth token
    response = await async_client.post(
        "/auth/token",
        data={"username": test_user.username, "password": "test"},
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

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
    assert call_kwargs['discipline'] == "PT"
    assert str(call_kwargs['start_date']) == "2023-01-01"
    assert str(call_kwargs['end_date']) == "2023-01-31"

    mock_crud.get_team_habit_summary.assert_awaited_once()
    call_kwargs = mock_crud.get_team_habit_summary.call_args.kwargs
    assert call_kwargs['discipline'] == "PT"

    mock_crud.get_clinician_habit_breakdown.assert_awaited_once()
    call_kwargs = mock_crud.get_clinician_habit_breakdown.call_args.kwargs
    assert call_kwargs['discipline'] == "PT"