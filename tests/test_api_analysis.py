# MODIFIED: Refactored to use a proper pytest fixture for patching.
# ruff: noqa: E402
import os
import sys
from datetime import UTC, datetime
import types
from unittest.mock import AsyncMock, MagicMock, patch

from typing import cast

import pytest

# This test is marked as "heavy" because it involves the entire application stack
# and requires extensive mocking to run in isolation. It is intended for end-to-end validation.
pytestmark = pytest.mark.heavy

# Ensure the src directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

sys.modules['transformers'] = types.ModuleType('transformers')
sys.modules['transformers'].pipeline = MagicMock()
sys.modules['transformers'].AutoModelForTokenClassification = MagicMock()
sys.modules['transformers'].AutoTokenizer = MagicMock()

sys.modules['transformers.configuration_utils'] = types.ModuleType('transformers.configuration_utils')
sys.modules['transformers.configuration_utils'].PretrainedConfig = MagicMock()

sys.modules['transformers.utils'] = types.ModuleType('transformers.utils')
sys.modules['transformers'].utils = sys.modules['transformers.utils']
sys.modules['transformers.utils'].logging = MagicMock()

# 1. Mock the modules that are missing from the codebase.
MOCK_MODULES = {
    "src.core.nlg_service": MagicMock(),
    "src.core.risk_scoring_service": MagicMock(),
    "src.core.preprocessing_service": MagicMock(),
    "ctransformers": MagicMock(),
    "sentence_transformers": MagicMock(),
}
sys.modules.update(MOCK_MODULES)


@pytest.fixture(scope="session", autouse=True)
def mock_preemptive_services():
    """Manually start and stop patches for services called on app import."""
    patchers = [
        patch(
            "ctransformers.AutoModelForCausalLM.from_pretrained",
            return_value=MagicMock(),
        ),
        patch("transformers.pipeline", return_value=MagicMock()),
        patch("src.database.crud.get_rubric", return_value=None),  # Prevent DB calls
        patch("src.core.hybrid_retriever.SentenceTransformer", return_value=MagicMock()),
        patch("src.core.hybrid_retriever.BM25Okapi", return_value=MagicMock()),
    ]
    for p in patchers:
        p.start()
    yield
    for p in patchers:
        p.stop()


# --- Test Code ---
# Now it is safe to import the rest of our test modules and the application itself.
from fastapi.testclient import TestClient

from src.api.main import app, limiter
from src.api.routers import analysis as analysis_router
from src.auth import get_current_active_user
from src.database import schemas

# Disable rate limiting for all tests
limiter.enabled = False


@pytest.fixture(autouse=True)
def reset_analysis_state():
    """Ensure shared task registries start clean across tests."""
    analysis_router.tasks.clear()
    analysis_router.analysis_task_registry.metadata.clear()
    yield
    analysis_router.tasks.clear()
    analysis_router.analysis_task_registry.metadata.clear()


@pytest.fixture(scope="module")
def client():
    """Create a TestClient for the API, with authentication overridden."""
    dummy_user = schemas.User(
        id=1,
        username="testuser",
        is_active=True,
        is_admin=False,
        created_at=datetime.now(UTC),
    )

    def override_get_current_active_user():
        return dummy_user

    app.dependency_overrides[get_current_active_user] = override_get_current_active_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides = {}


def test_analyze_document_api_route(client: TestClient, mocker, tmp_path):
    """POST /analysis/analyze yields a task id and enqueues background work."""
    mock_run_analysis = mocker.patch("src.api.routers.analysis.run_analysis_and_save", return_value=None)

    file_path = tmp_path / "test_note.txt"
    file_path.write_text("This is a test document.")

    with file_path.open("rb") as f:
        response = client.post(
            "/analysis/analyze",
            files={"file": (file_path.name, f, "text/plain")},
            data={"discipline": "pt", "analysis_mode": "rubric"},
        )

    assert response.status_code == 202
    response_data = response.json()
    assert "task_id" in response_data
    assert response_data["status"] == "processing"

    mock_run_analysis.assert_called_once_with(
        mocker.ANY,
        response_data["task_id"],
        file_path.name,
        "pt",
        "rubric",
        "standard",
        mocker.ANY,
    )


def test_analyze_document_rejects_invalid_strictness(client: TestClient, tmp_path):
    file_path = tmp_path / "invalid.txt"
    file_path.write_text("bad strictness")

    with file_path.open("rb") as f:
        response = client.post(
            "/analysis/analyze",
            files={"file": (file_path.name, f, "text/plain")},
            data={
                "discipline": "pt",
                "analysis_mode": "rubric",
                "strictness": "ultra",
            },
        )

    assert response.status_code == 400
    payload = response.json() if response.headers.get('content-type') == 'application/json' else {}
    assert isinstance(payload, dict)
    message = cast(str | None, payload.get('detail') or payload.get('message'))
    assert message is not None and 'Invalid strictness' in message


def test_analyze_document_rejects_oversized_file(client: TestClient, mocker, tmp_path):
    file_path = tmp_path / "oversize.txt"
    file_path.write_text("pretend data")

    mocker.patch(
        "src.api.routers.analysis.SecurityValidator.validate_file_size",
        return_value=(False, "too big"),
    )

    with file_path.open("rb") as f:
        response = client.post(
            "/analysis/analyze",
            files={"file": (file_path.name, f, "text/plain")},
            data={"discipline": "pt", "analysis_mode": "rubric", "strictness": "standard"},
        )

    assert response.status_code == 400
    payload = response.json() if response.headers.get('content-type') == 'application/json' else {}
    assert isinstance(payload, dict)
    message = cast(str | None, payload.get('detail') or payload.get('message'))
    assert message == 'too big'


@pytest.mark.asyncio
async def test_run_analysis_and_save_persists_strictness_and_metadata(mocker):
    task_id = "task-123"

    analysis_service = MagicMock()
    analysis_service.analyze_document = AsyncMock(
        return_value={
            "analysis": {
                "findings": ["issue"],
                "compliance_score": 82,
                "document_type": "note",
            },
            "report_html": "<html></html>",
        }
    )

    async def immediate_start(task_id_arg: str, coroutine):
        assert task_id_arg == task_id
        return await coroutine

    start_mock = AsyncMock(side_effect=immediate_start)
    mocker.patch.object(analysis_router.analysis_task_registry, "start", start_mock)
    mocker.patch("src.api.routers.analysis.asyncio.sleep", AsyncMock())

    await analysis_router.run_analysis_and_save(
        file_content=b"content",
        task_id=task_id,
        original_filename="note.txt",
        discipline="pt",
        analysis_mode="rubric",
        strictness="lenient",
        analysis_service=analysis_service,
    )

    start_mock.assert_awaited_once()
    analysis_service.analyze_document.assert_awaited_once()
    assert analysis_service.analyze_document.await_args.kwargs["strictness"] == "lenient"

    task_state = analysis_router.tasks[task_id]
    assert task_state["status"] == "completed"
    assert task_state["strictness"] == "lenient"
    assert task_state["status_message"] == "Analysis complete."
