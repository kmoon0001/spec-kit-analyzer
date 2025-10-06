# ruff: noqa: E402
import os
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

# This test is marked as 'heavy' because it involves the entire application stack
# and requires extensive mocking to run in isolation. It is intended for end-to-end validation.
pytestmark = pytest.mark.heavy

# --- Pre-emptive Mocking ---
# This code MUST run before the application is imported. We cannot use pytest
# fixtures for this, as they run after module import.

# Ensure the src directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 1. Mock the modules that are missing from the codebase.
MOCK_MODULES = {
    "src.core.nlg_service": MagicMock(),
    "src.core.risk_scoring_service": MagicMock(),
    "src.core.preprocessing_service": MagicMock(),
    "ctransformers": MagicMock(),
    "transformers": MagicMock(),
}
sys.modules.update(MOCK_MODULES)

# 2. Manually start patches for all external-facing services and functions
#    that are called during the application's import-time initialization.
#    This prevents any network calls or heavy model loading.
patchers = [
    patch(
        "ctransformers.AutoModelForCausalLM.from_pretrained",
        return_value=MagicMock(),
    ),
    patch("transformers.pipeline", return_value=MagicMock()),
    patch("transformers.pipeline", return_value=MagicMock()),
    patch("src.database.crud.get_rubrics", return_value=[]),  # Prevent DB calls
    patch("src.core.hybrid_retriever.SentenceTransformer", return_value=MagicMock()),
    patch("src.core.hybrid_retriever.BM25Okapi", return_value=MagicMock()),
]
for p in patchers:
    p.start()

# --- Test Code ---
# Now it is safe to import the rest of our test modules and the application itself.
from fastapi.testclient import TestClient

from src.api.main import app, limiter
from src.auth import get_current_active_user
from src.database import schemas


# We must stop the patchers we started manually. A session-scoped autouse fixture
# is a clean way to do this at the end of the test run.
@pytest.fixture(scope="session", autouse=True)
def stop_manual_patchers():
    """Stops the manually started patchers at the end of the test session."""
    yield
    for p in patchers:
        p.stop()


# Disable rate limiting for all tests
limiter.enabled = False


@pytest.fixture(scope="module")
def client():
    """Create a TestClient for the API, with authentication overridden."""
    # Define a dummy user model that matches the User schema
    dummy_user = schemas.User(
        id=1,
        username="testuser",
        is_active=True,
        is_admin=False,
        created_at=datetime.now(timezone.utc),
    )

    def override_get_current_active_user():
        return dummy_user

    app.dependency_overrides[get_current_active_user] = override_get_current_active_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides = {}


def test_analyze_document_api_route(client: TestClient, mocker):
    """
    Tests the POST /analysis/analyze API endpoint.
    This test verifies the API logic, file handling, and background task creation.
    """
    # Mock the background task function to check if it's called correctly.
    mock_run_analysis = mocker.patch(
        "src.api.routers.analysis.run_analysis_and_save", return_value=None
    )

    dummy_filename = "test_note.txt"
    with open(dummy_filename, "w") as f:
        f.write("This is a test document.")

    try:
        with open(dummy_filename, "rb") as f:
            response = client.post(
                "/analysis/analyze",
                files={"file": (dummy_filename, f, "text/plain")},
                data={"discipline": "pt", "analysis_mode": "rubric"},
            )
    finally:
        os.remove(dummy_filename)

    assert response.status_code == 202
    response_data = response.json()
    assert "task_id" in response_data
    assert response_data["status"] == "processing"

    # Verify that the background task was called once with the correct arguments.
    # We use mocker.ANY for values that are generated at runtime (e.g., file paths, services).
    mock_run_analysis.assert_called_once_with(
        mocker.ANY,
        response_data["task_id"],
        dummy_filename,
        "pt",
        "rubric",
        mocker.ANY,
    )
