import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_rubric(authenticated_admin_client: AsyncClient):
    rubric_data = {
        "name": "Test Rubric",
        "discipline": "PT",
        "category": "Test",
        "regulation": "Test Regulation",
        "common_pitfalls": "Test Pitfalls",
        "best_practice": "Test Best Practice",
    }
    response = await authenticated_admin_client.post("/rubrics/", json=rubric_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Rubric"
    assert data["value"] == data["id"]


@pytest.mark.asyncio
async def test_read_rubrics_requires_active_user(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/rubrics/")
    assert response.status_code == 200
    payload = response.json()
    assert "rubrics" in payload
    assert isinstance(payload["rubrics"], list)


@pytest.mark.asyncio
async def test_read_rubric(authenticated_admin_client: AsyncClient):
    rubric_data = {
        "name": "Test Rubric to Read",
        "discipline": "PT",
        "category": "Test",
        "regulation": "Test Regulation",
        "common_pitfalls": "Test Pitfalls",
        "best_practice": "Test Best Practice",
    }
    response = await authenticated_admin_client.post("/rubrics/", json=rubric_data)
    assert response.status_code == 200
    rubric_id = response.json()["id"]

    response = await authenticated_admin_client.get(f"/rubrics/{rubric_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Rubric to Read"
    assert data["value"] == rubric_id


@pytest.mark.asyncio
async def test_unauthorized_create_still_allows_read(authenticated_client: AsyncClient):
    rubric_data = {
        "name": "Unauthorized Rubric",
        "discipline": "PT",
        "category": "Test",
        "regulation": "Test Regulation",
        "common_pitfalls": "Test Pitfalls",
        "best_practice": "Test Best Practice",
    }
    response = await authenticated_client.post("/rubrics/", json=rubric_data)
    assert response.status_code == 403

    response = await authenticated_client.get("/rubrics/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_rubric(authenticated_admin_client: AsyncClient):
    rubric_data = {
        "name": "Test Rubric to Update",
        "discipline": "PT",
        "category": "Test",
        "regulation": "Test Regulation",
        "common_pitfalls": "Test Pitfalls",
        "best_practice": "Test Best Practice",
    }
    response = await authenticated_admin_client.post("/rubrics/", json=rubric_data)
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
    response = await authenticated_admin_client.put(
        f"/rubrics/{rubric_id}", json=updated_rubric_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Rubric"
    assert data["value"] == rubric_id


@pytest.mark.asyncio
async def test_delete_rubric(authenticated_admin_client: AsyncClient):
    rubric_data = {
        "name": "Test Rubric to Delete",
        "discipline": "PT",
        "category": "Test",
        "regulation": "Test Regulation",
        "common_pitfalls": "Test Pitfalls",
        "best_practice": "Test Best Practice",
    }
    response = await authenticated_admin_client.post("/rubrics/", json=rubric_data)
    assert response.status_code == 200
    rubric_id = response.json()["id"]

    response = await authenticated_admin_client.delete(f"/rubrics/{rubric_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["value"] == rubric_id

    response = await authenticated_admin_client.get(f"/rubrics/{rubric_id}")
    assert response.status_code == 404
