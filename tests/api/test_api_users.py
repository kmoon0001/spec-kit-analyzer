import pytest

pytest.importorskip("sqlalchemy")

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import crud, schemas
from src.auth import AuthService
from unittest.mock import patch


@pytest.mark.asyncio
async def test_update_current_user_password(client: AsyncClient, db_session: AsyncSession):
    # Create a user
    user_create = schemas.UserCreate(username="testuser_pass", password="password")
    hashed_password = AuthService().get_password_hash(user_create.password)
    user = await crud.create_user(db_session, user_create, hashed_password)

    # Log in to get a token
    login_data = {"username": user.username, "password": "password"}
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Update the password
    headers = {"Authorization": f"Bearer {token}"}
    password_data = {"old_password": "password", "new_password": "new_password"}

    with patch("src.auth.get_current_active_user", return_value=user):
        response = await client.put("/users/me/password", json=password_data, headers=headers)

    assert response.status_code == 204

    # Verify the password was changed by trying to log in with the new password
    login_data = {"username": user.username, "password": "new_password"}
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
