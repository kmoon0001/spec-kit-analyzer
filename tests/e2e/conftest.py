"""
E2E Test Configuration and Fixtures

Provides shared fixtures and configuration for end-to-end testing.
"""

import asyncio
import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient

# Import application components
from src.api.main import app
from src.config import get_settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Test-specific settings configuration."""
    settings = get_settings()
    # Override settings for testing
    settings.database_url = "sqlite:///./test_e2e.db"
    settings.testing = True
    return settings


@pytest.fixture(scope="session")
def test_client(test_settings, test_db) -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI application."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
async def test_db(test_settings):
    """Create a test database for E2E testing."""
    from sqlalchemy.exc import IntegrityError

    from src.database import crud, schemas
    from src.database.database import AsyncSessionLocal, Base, engine

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default rubrics so end-to-end workflows have options
    async with AsyncSessionLocal() as session:
        default_rubrics = [
            schemas.RubricCreate(
                name="PT Compliance Test Rubric",
                discipline="PT",
                category="Default",
                regulation="Standard PT compliance rubric",
                common_pitfalls="Missing subjective/objective data",
                best_practice="Document all SOAP sections",
            ),
        ]
        for rubric in default_rubrics:
            try:
                await crud.create_rubric(session, rubric)
            except IntegrityError:
                await session.rollback()

    yield

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "username": "test_therapist",
        "email": "test@example.com",
        "password": "test_password_123",
        "is_admin": False,
    }


@pytest.fixture
def test_document_content():
    """Sample document content for testing."""
    return """
    PHYSICAL THERAPY PROGRESS NOTE

    Patient: John Doe (DOB: 01/01/1980)
    Date: 2024-01-15
    Therapist: Jane Smith, PT

    SUBJECTIVE:
    Patient reports decreased pain in lower back from 8/10 to 5/10 since last visit.
    States he is able to walk longer distances without significant discomfort.

    OBJECTIVE:
    Range of Motion: Lumbar flexion 45 degrees (improved from 30 degrees)
    Strength: Hip flexors 4/5, Hip extensors 4/5
    Functional: Able to sit to stand with minimal assistance

    ASSESSMENT:
    Patient demonstrates good progress with current treatment plan.
    Functional improvements noted in mobility and pain management.

    PLAN:
    Continue current exercise program
    Progress to more challenging strengthening exercises
    Patient education on home exercise program
    Next appointment in 1 week
    """


@pytest.fixture
def test_rubric_data():
    """Sample rubric data for testing."""
    return {
        "name": "PT Compliance Test Rubric",
        "discipline": "pt",
        "rules": [
            {
                "id": "subjective_required",
                "description": "Progress note must include subjective section",
                "pattern": r"SUBJECTIVE:",
                "severity": "high",
            },
            {
                "id": "objective_measurements",
                "description": "Objective section must include measurable data",
                "pattern": r"Range of Motion|Strength|Functional",
                "severity": "medium",
            },
            {
                "id": "assessment_present",
                "description": "Assessment section must be present",
                "pattern": r"ASSESSMENT:",
                "severity": "high",
            },
            {
                "id": "plan_documented",
                "description": "Plan section must be documented",
                "pattern": r"PLAN:",
                "severity": "high",
            },
        ],
    }


@pytest.fixture
def temp_upload_dir():
    """Create a temporary directory for file uploads."""
    temp_dir = tempfile.mkdtemp(prefix="e2e_test_uploads_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_document_file(temp_upload_dir, test_document_content):
    """Create a sample document file for testing."""
    doc_file = temp_upload_dir / "test_progress_note.txt"
    doc_file.write_text(test_document_content)
    return doc_file


@pytest.fixture
def mock_ai_services():
    """Mock AI services for faster testing."""
    mocks = {"llm_service": Mock(), "ner_service": Mock(), "embedding_service": Mock(), "compliance_analyzer": Mock()}

    # Configure mock responses
    mocks["llm_service"].generate_response.return_value = {
        "response": "This is a mock AI response for testing.",
        "confidence": 0.85,
    }

    mocks["compliance_analyzer"].analyze.return_value = {
        "findings": [
            {
                "id": "test_finding_1",
                "title": "Test Compliance Issue",
                "description": "This is a test compliance finding",
                "severity": "medium",
                "confidence": 0.8,
                "evidence": "Test evidence text",
            }
        ],
        "overall_score": 75,
        "document_type": "progress_note",
    }

    return mocks


@pytest.fixture
def authenticated_headers(test_client, test_user_data):
    """Get authentication headers for API requests."""
    # Create test user
    response = test_client.post("/auth/register", json=test_user_data)
    assert response.status_code in [200, 201, 409]  # 409 if user already exists

    # Login to get token
    login_data = {"username": test_user_data["username"], "password": test_user_data["password"]}
    response = test_client.post("/auth/token", data=login_data)
    assert response.status_code == 200

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def e2e_test_config():
    """Configuration for E2E tests."""
    return {
        "api_base_url": "http://testserver",
        "timeout": 30,
        "max_retries": 3,
        "test_data_dir": Path(__file__).parent / "test_data",
        "performance_thresholds": {
            "document_analysis": 120,  # seconds
            "api_response": 5,  # seconds
            "pdf_export": 30,  # seconds
        },
    }


class E2ETestHelper:
    """Helper class for common E2E test operations."""

    def __init__(self, client: TestClient, headers: dict[str, str]):
        self.client = client
        self.headers = headers

    def upload_document(self, file_path: Path) -> dict[str, Any]:
        """Upload a document and return the response."""
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "text/plain")}
            response = self.client.post("/upload-document", files=files, headers=self.headers)
        return response.json()

    def start_analysis(self, document_id: str, rubric_id: str) -> dict[str, Any]:
        """Start document analysis and return task ID."""
        data = {"document_id": document_id, "rubric_id": rubric_id, "analysis_type": "comprehensive"}
        response = self.client.post("/analyze", json=data, headers=self.headers)
        return response.json()

    def wait_for_analysis(self, task_id: str, timeout: int = 120) -> dict[str, Any]:
        """Wait for analysis to complete and return results."""
        import time

        start_time = time.time()

        while time.time() - start_time < timeout:
            response = self.client.get(f"/analysis-status/{task_id}", headers=self.headers)
            result = response.json()

            if result.get("status") == "completed":
                return result
            elif result.get("status") == "failed":
                raise Exception(f"Analysis failed: {result.get('error')}")

            time.sleep(2)

        raise TimeoutError(f"Analysis did not complete within {timeout} seconds")


@pytest.fixture
def e2e_helper(test_client, authenticated_headers):
    """Create an E2E test helper instance."""
    return E2ETestHelper(test_client, authenticated_headers)
