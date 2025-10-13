import os
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_analysis_service
from src.api.main import app
from src.auth import get_current_active_user
from src.database import Base, get_async_db, models

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_read_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Clinical Compliance Analyzer API"}


@pytest.mark.asyncio
@patch("src.api.routers.analysis.run_analysis_and_save")
async def test_analyze_document_endpoint(mock_run_analysis, client: AsyncClient):
    file_content = b"This is a test document."
    response = await client.post("/analysis/analyze", files={"file": ("test.txt", file_content, "text/plain")})
    assert response.status_code == 202
    response_json = response.json()
    assert "task_id" in response_json
    assert response_json["status"] == "processing"
    assert mock_run_analysis.called


@pytest.mark.asyncio
async def test_get_dashboard_reports_endpoint_empty(client: AsyncClient):
    response = await client.get("/dashboard/reports")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json() == []
