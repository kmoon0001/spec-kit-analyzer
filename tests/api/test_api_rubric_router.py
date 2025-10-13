import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import crud, schemas
from src.auth import AuthService

@pytest.mark.asyncio
async def test_create_rubric(client: AsyncClient, db_session: AsyncSession):
    # Create an admin user and log in
    admin_user_create = schemas.UserCreate(username="admin_rubric", password="password", is_admin=True)
    hashed_password = AuthService().get_password_hash(admin_user_create.password)
    admin_user = await crud.create_user(db_session, admin_user_create, hashed_password)
    login_data = {"username": admin_user.username, "password": "password"}
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Create a rubric
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
    assert "id" in data

@pytest.mark.asyncio
async def test_read_rubrics(client: AsyncClient, db_session: AsyncSession):
    # Create an admin user and log in
    admin_user_create = schemas.UserCreate(username="admin_rubric_read", password="password", is_admin=True)
    hashed_password = AuthService().get_password_hash(admin_user_create.password)
    admin_user = await crud.create_user(db_session, admin_user_create, hashed_password)
    login_data = {"username": admin_user.username, "password": "password"}
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Read rubrics
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/rubrics/", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient, db_session: AsyncSession):
    # Create a regular user and log in
    user_create = schemas.UserCreate(username="regular_rubric", password="password")
    hashed_password = AuthService().get_password_hash(user_create.password)
    user = await crud.create_user(db_session, user_create, hashed_password)
    login_data = {"username": user.username, "password": "password"}
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Try to create a rubric
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

@pytest.mark.asyncio
async def test_read_rubric(client: AsyncClient, db_session: AsyncSession):
    # Create an admin user and log in
    admin_user_create = schemas.UserCreate(username="admin_rubric_read_one", password="password", is_admin=True)
    hashed_password = AuthService().get_password_hash(admin_user_create.password)
    admin_user = await crud.create_user(db_session, admin_user_create, hashed_password)
    login_data = {"username": admin_user.username, "password": "password"}
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Create a rubric to read
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

    # Read the rubric
    response = await client.get(f"/rubrics/{rubric_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Rubric to Read"

@pytest.mark.asyncio
async def test_update_rubric(client: AsyncClient, db_session: AsyncSession):
    # Create an admin user and log in
    admin_user_create = schemas.UserCreate(username="admin_rubric_update", password="password", is_admin=True)
    hashed_password = AuthService().get_password_hash(admin_user_create.password)
    admin_user = await crud.create_user(db_session, admin_user_create, hashed_password)
    login_data = {"username": admin_user.username, "password": "password"}
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Create a rubric to update
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

    # Update the rubric
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

@pytest.mark.asyncio
async def test_delete_rubric(client: AsyncClient, db_session: AsyncSession):
    # Create an admin user and log in
    admin_user_create = schemas.UserCreate(username="admin_rubric_delete", password="password", is_admin=True)
    hashed_password = AuthService().get_password_hash(admin_user_create.password)
    admin_user = await crud.create_user(db_session, admin_user_create, hashed_password)
    login_data = {"username": admin_user.username, "password": "password"}
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Create a rubric to delete
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

    # Delete the rubric
    response = await client.delete(f"/rubrics/{rubric_id}", headers=headers)
    assert response.status_code == 200

    # Verify it was deleted
    response = await client.get(f"/rubrics/{rubric_id}", headers=headers)
    assert response.status_code == 404