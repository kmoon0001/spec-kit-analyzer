import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_update_current_user_password(
    authenticated_client: AsyncClient,
):
    # Update the password
    password_data = {"old_password": "testpassword", "new_password": "new_password"}
    response = await authenticated_client.put(
        "/users/me/password", json=password_data
    )
    assert response.status_code == 204

    # Verify the password was changed by trying to log in with the new password
    login_data = {"username": "testuser", "password": "new_password"}
    response = await authenticated_client.post("/auth/login", data=login_data)
    assert response.status_code == 200
