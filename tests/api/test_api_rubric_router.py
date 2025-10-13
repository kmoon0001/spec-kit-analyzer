import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import AuthService
from src.database import crud, schemas


async def _create_and_login_user(client: AsyncClient, db_session: AsyncSession, *, username: str, is_admin: bool) -> str:
    user_data = schemas.UserCreate(username=username, password="password", is_admin=is_admin)
    hashed_password = AuthService().get_password_hash(user_data.password)
    await crud.create_user(db_session, user_data, hashed_password)
    login_data = {"username": user_data.username, "password": "password"}
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_rubric(client: AsyncClient, db_session: AsyncSession):
    token = await _create_and_login_user(client, db_session, username="admin_rubric", is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}

    rubric_data = {
        "name": "Test Rubric",
        "discipline": "PT",
        "category": "Test",
        "regulation": "Test Regulation",
        "common_pitfalls": "Test Pitfalls",
        "best_practice": "Test Best Practice",
    }
    response = await client.post("/rubrics/", json=rubric_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Rubric"
    assert data["value"] == data["id"]


@pytest.mark.asyncio
async def test_read_rubrics_requires_active_user(client: AsyncClient, db_session: AsyncSession):
    token = await _create_and_login_user(client, db_session, username="regular_reader", is_admin=False)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/rubrics/", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert "rubrics" in payload
    assert isinstance(payload["rubrics"], list)


@pytest.mark.asyncio
async def test_read_rubric(client: AsyncClient, db_session: AsyncSession):
    token = await _create_and_login_user(client, db_session, username="admin_rubric_read_one", is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}

    rubric_data = {
        "name": "Test Rubric to Read",
        "discipline": "PT",
        "category": "Test",
        "regulation": "Test Regulation",
        "common_pitfalls": "Test Pitfalls",
        "best_practice": "Test Best Practice",
    }
    response = await client.post("/rubrics/", json=rubric_data, headers=headers)
    assert response.status_code == 200
    rubric_id = response.json()["id"]

    response = await client.get(f"/rubrics/{rubric_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Rubric to Read"
    assert data["value"] == rubric_id


@pytest.mark.asyncio
async def test_unauthorized_create_still_allows_read(client: AsyncClient, db_session: AsyncSession):
    token = await _create_and_login_user(client, db_session, username="regular_rubric", is_admin=False)
    headers = {"Authorization": f"Bearer {token}"}

    rubric_data = {
        "name": "Unauthorized Rubric",
        "discipline": "PT",
        "category": "Test",
        "regulation": "Test Regulation",
        "common_pitfalls": "Test Pitfalls",
        "best_practice": "Test Best Practice",
    }
    response = await client.post("/rubrics/", json=rubric_data, headers=headers)
    assert response.status_code == 403

    response = await client.get("/rubrics/", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_rubric(client: AsyncClient, db_session: AsyncSession):
    token = await _create_and_login_user(client, db_session, username="admin_rubric_update", is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}

    rubric_data = {
        "name": "Test Rubric to Update",
        "discipline": "PT",
        "category": "Test",
        "regulation": "Test Regulation",
        "common_pitfalls": "Test Pitfalls",
        "best_practice": "Test Best Practice",
    }
    response = await client.post("/rubrics/", json=rubric_data, headers=headers)
    assert response.status_code == 200
    rubric_id = response.json()["id"]

    updated_rubric_data = {
        "name": "Updated Rubric",
        "discipline": "OT",
        "category": "Updated",
        "regulation": "Updated Regulation",
        "common_pitfalls": "Updated Pitfalls",
        "best_practice": "Updated Best Practice",
    }
    response = await client.put(f"/rubrics/{rubric_id}", json=updated_rubric_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Rubric"
    assert data["value"] == rubric_id


@pytest.mark.asyncio
async def test_delete_rubric(client: AsyncClient, db_session: AsyncSession):
    token = await _create_and_login_user(client, db_session, username="admin_rubric_delete", is_admin=True)
    headers = {"Authorization": f"Bearer {token}"}

    rubric_data = {
        "name": "Test Rubric to Delete",
        "discipline": "PT",
        "category": "Test",
        "regulation": "Test Regulation",
        "common_pitfalls": "Test Pitfalls",
        "best_practice": "Test Best Practice",
    }
    response = await client.post("/rubrics/", json=rubric_data, headers=headers)
    assert response.status_code == 200
    rubric_id = response.json()["id"]

    response = await client.delete(f"/rubrics/{rubric_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["value"] == rubric_id

    response = await client.get(f"/rubrics/{rubric_id}", headers=headers)
    assert response.status_code == 404
