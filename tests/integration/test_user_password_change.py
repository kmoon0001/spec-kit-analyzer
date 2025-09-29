import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import crud, schemas
from src.api.main import app  # Import your FastAPI app
from tests.conftest import test_user_credentials


@pytest.mark.asyncio
async def test_update_current_user_password(
    async_client: AsyncClient, test_db: AsyncSession, test_user
):
    """
    Test that a user can successfully change their password.
    """
    # 1. Log in to get an auth token for the test user
    login_data = {
        "username": test_user_credentials["username"],
        "password": test_user_credentials["password"],
    }
    response = await async_client.post("/auth/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Define the new password
    new_password = "new_secure_password"
    password_update_data = {
        "old_password": test_user_credentials["password"],
        "new_password": new_password,
    }

    # 3. Make the request to change the password
    response = await async_client.put(
        "/users/me/password", json=password_update_data, headers=headers
    )

    # 4. Assert the request was successful
    assert response.status_code == 204, f"Failed to update password: {response.text}"

    # 5. Verify the password was actually changed by trying to log in with the new password
    new_login_data = {"username": test_user.username, "password": new_password}
    response = await async_client.post("/auth/token", data=new_login_data)
    assert response.status_code == 200, "Login with new password failed"


@pytest.mark.asyncio
async def test_update_password_incorrect_old_password(
    async_client: AsyncClient, test_user
):
    """
    Test that changing a password with an incorrect old password fails.
    """
    # 1. Log in to get an auth token for the test user
    login_data = {
        "username": test_user_credentials["username"],
        "password": test_user_credentials["password"],
    }
    response = await async_client.post("/auth/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Attempt to change the password with an incorrect old password
    password_update_data = {
        "old_password": "wrong_old_password",
        "new_password": "a_new_password",
    }

    response = await async_client.put(
        "/users/me/password", json=password_update_data, headers=headers
    )

    # 3. Assert that the request fails with a 400 Bad Request error
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect old password."