"""Offline-friendly mock API surface used by the test-suite.

This module intentionally avoids importing heavyweight third-party dependencies
so that it can be executed in constrained CI environments.  When FastAPI is
available it exposes a small application instance compatible with the real API
and returns a ``TestClient`` for callers.  When FastAPI is missing, it falls
back to a lightweight in-process client that mimics the subset of the
``TestClient`` interface used by the tests (``post``/``get`` with ``json`` and
``status_code`` accessors).
"""

from __future__ import annotations

import copy
import datetime as dt
import io
import json
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

try:  # pragma: no cover - FastAPI is optional in the offline CI image
    from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
    from fastapi.testclient import TestClient

    _FASTAPI_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - executed when FastAPI is absent
    FastAPI = None  # type: ignore[misc]
    UploadFile = Any  # type: ignore[misc]
    TestClient = None  # type: ignore[misc]
    _FASTAPI_AVAILABLE = False

try:  # pragma: no cover - importing the real schemas may fail when deps are missing
    from src.database import schemas
except Exception:  # pragma: no cover - fallback for offline execution

    @dataclass
    class _FallbackUser:
        id: int
        username: str
        is_active: bool = True
        is_admin: bool = False

    class _FallbackSchemasModule:
        User = _FallbackUser

    schemas = _FallbackSchemasModule()  # type: ignore[assignment]


class MockAnalysisService:
    """Deterministic stand-in for the production analysis pipeline."""

    async def analyze_document(
        self,
        *,
        file_content: bytes,
        original_filename: str,
        discipline: str,
        analysis_mode: str,
    ) -> dict[str, Any]:
        if not file_content:
            raise ValueError("Cannot analyse an empty document")

        timestamp = dt.datetime.now(dt.UTC)

        return {
            "analysis": {
                "document_name": original_filename,
                "discipline": discipline.lower(),
                "analysis_mode": analysis_mode.lower(),
                "summary": "Mock compliance analysis generated for testing purposes.",
                "compliance_score": 75.0,
                "findings": [
                    {
                        "rule_id": "MOCK-001",
                        "title": "Plan of care details incomplete",
                        "description": ("Documentation is missing measurable objectives for the therapy plan."),
                        "recommendation": "Add at least one measurable functional goal to the plan.",
                        "severity": "moderate",
                    }
                ],
            },
            "report_html": "<h1>Mock Compliance Report</h1><p>Generated for offline validation.</p>",
            "generated_at": timestamp.isoformat(),
        }


_mock_analysis_service = MockAnalysisService()
_tasks: dict[str, dict[str, Any]] = {}


def reset_mock_tasks() -> None:
    """Utility used by tests to clear the in-memory task registry."""

    _tasks.clear()


def get_mock_analysis_service() -> MockAnalysisService:
    return _mock_analysis_service


def get_current_active_user() -> schemas.User:
    return schemas.User(id=1, username="mock-user", is_active=True, is_admin=False)


def _store_completed_task(*, task_id: str, filename: str, result: dict[str, Any], user: schemas.User) -> dict[str, Any]:
    timestamp = dt.datetime.now(dt.UTC)
    analysis_payload = copy.deepcopy(result)
    analysis_details = analysis_payload.get("analysis", {}) if isinstance(analysis_payload, dict) else {}

    task_entry = {
        "task_id": task_id,
        "status": "completed",
        "status_message": "Analysis complete.",
        "progress": 100,
        "filename": filename,
        "timestamp": timestamp,
        "requested_by": user.username,
        "result": analysis_payload,
        "analysis": analysis_details,
        "findings": analysis_details.get("findings", []),
        "overall_score": analysis_details.get("compliance_score"),
    }
    _tasks[task_id] = task_entry
    return task_entry


# ---------------------------------------------------------------------------
# FastAPI implementation (used when the dependency is available)
# ---------------------------------------------------------------------------

if _FASTAPI_AVAILABLE:  # pragma: no cover - exercised only when FastAPI exists
    app = FastAPI(title="Therapy Compliance Analyzer (Mock API)")

    @app.post("/analysis/analyze", status_code=202)
    async def analyze_document(
        file: UploadFile = File(...),
        discipline: str = Form("pt"),
        analysis_mode: str = Form("rubric"),
        current_user: schemas.User = Depends(get_current_active_user),
        analysis_service: MockAnalysisService = Depends(get_mock_analysis_service),
    ) -> dict[str, str]:
        if not current_user.is_active:
            raise HTTPException(status_code=403, detail="Inactive users cannot request analysis")

        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Uploaded document is empty")

        original_filename = file.filename or "uploaded_document.txt"
        try:
            result = await analysis_service.analyze_document(
                file_content=file_content,
                original_filename=original_filename,
                discipline=discipline,
                analysis_mode=analysis_mode,
            )
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        task_id = uuid.uuid4().hex
        # Ensure result is properly awaited dict, not coroutine
        analysis_result: dict[str, Any] = result
        _store_completed_task(task_id=task_id, filename=original_filename, result=analysis_result, user=current_user)
        return {"task_id": task_id, "status": "processing"}

    @app.get("/analysis/status/{task_id}")
    async def get_analysis_status(
        task_id: str, current_user: schemas.User = Depends(get_current_active_user)
    ) -> dict[str, Any]:
        if not current_user.is_active:
            raise HTTPException(status_code=403, detail="Inactive users cannot view task status")

        task = _tasks.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")

        return copy.deepcopy(task)

    @contextmanager
    def create_mock_test_client(user: schemas.User | None = None) -> Iterator[TestClient]:
        """Yield a :class:`TestClient` bound to the FastAPI app."""

        override_user = user or get_current_active_user()

        def override_dependency() -> schemas.User:
            return override_user

        app.dependency_overrides[get_current_active_user] = override_dependency
        try:
            with TestClient(app) as client:
                yield client
        finally:
            app.dependency_overrides.clear()
            reset_mock_tasks()

else:

    @dataclass(slots=True)
    class _MockResponse:
        status_code: int
        _payload: dict[str, Any]

        def json(self) -> dict[str, Any]:
            return copy.deepcopy(self._payload)

        @property
        def text(self) -> str:
            return json.dumps(self._payload)

    class _OfflineClient:
        """Minimal TestClient look-alike used when FastAPI is unavailable."""

        def __init__(self, user_provider: Callable[[], schemas.User]):
            self._user_provider = user_provider

        def post(
            self,
            path: str,
            *,
            files: dict[str, tuple[str, io.BufferedReader, str]],
            data: dict[str, str],
            headers: Any | None = None,
        ) -> _MockResponse:  # noqa: ANN401
            if path != "/analysis/analyze":
                return _MockResponse(404, {"detail": "Endpoint not found"})

            file_tuple = files.get("file")
            if not file_tuple:
                return _MockResponse(400, {"detail": "File payload missing"})

            filename, file_obj, _content_type = file_tuple
            file_content = file_obj.read()
            discipline = data.get("discipline", "pt")
            analysis_mode = data.get("analysis_mode", "rubric")

            current_user = self._user_provider()
            if not current_user.is_active:
                return _MockResponse(403, {"detail": "Inactive users cannot request analysis"})

            try:
                result = await _mock_analysis_service.analyze_document(  # type: ignore[arg-type]
                    file_content=file_content,
                    original_filename=filename,
                    discipline=discipline,
                    analysis_mode=analysis_mode,
                )
                if hasattr(result, "__await__"):
                    result = result.__await__().__next__()  # type: ignore[assignment]
            except StopIteration as exc:  # pragma: no cover - defensive
                result = exc.value
            except ValueError as exc:
                return _MockResponse(400, {"detail": str(exc)})

            task_id = uuid.uuid4().hex
            # Ensure result is properly awaited dict, not coroutine
            mock_result: dict[str, Any] = result
            _store_completed_task(
                task_id=task_id,
                filename=filename or "uploaded_document.txt",
                result=mock_result,
                user=current_user,
            )
            return _MockResponse(202, {"task_id": task_id, "status": "processing"})

        def get(self, path: str, headers: Any | None = None) -> _MockResponse:  # noqa: ANN401
            if not path.startswith("/analysis/status/"):
                return _MockResponse(404, {"detail": "Endpoint not found"})

            task_id = path.rsplit("/", 1)[-1]
            current_user = self._user_provider()
            if not current_user.is_active:
                return _MockResponse(403, {"detail": "Inactive users cannot view task status"})

            task = _tasks.get(task_id)
            if task is None:
                return _MockResponse(404, {"detail": "Task not found"})

            return _MockResponse(200, copy.deepcopy(task))

    @contextmanager
    def create_offline_test_client(user: schemas.User | None = None) -> Iterator[_OfflineClient]:
        """Yield the offline client that mimics FastAPI's TestClient."""

        override_user = user or get_current_active_user()

        def user_provider() -> schemas.User:
            return override_user

        try:
            yield _OfflineClient(user_provider)
        finally:
            reset_mock_tasks()

    app = None  # type: ignore[assignment]


__all__ = [
    "MockAnalysisService",
    "create_mock_test_client",
    "get_current_active_user",
    "get_mock_analysis_service",
    "reset_mock_tasks",
]
