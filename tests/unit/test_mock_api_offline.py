import asyncio
import importlib
import io
import sys
import types

import pytest


def _reload_offline_mock_api(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delitem(sys.modules, "fastapi", raising=False)
    monkeypatch.delitem(sys.modules, "fastapi.testclient", raising=False)
    return importlib.reload(importlib.import_module("src.mock_api"))


def test_mock_analysis_service_generates_result(monkeypatch: pytest.MonkeyPatch):
    mock_api = _reload_offline_mock_api(monkeypatch)
    result = asyncio.run(
        mock_api.MockAnalysisService().analyze_document(
            file_content=b"content", original_filename="doc.txt", discipline="PT", analysis_mode="RUBRIC"
        )
    )

    assert result["analysis"]["document_name"] == "doc.txt"
    assert result["analysis"]["discipline"] == "pt"
    assert result["analysis"]["analysis_mode"] == "rubric"


def test_store_completed_task_tracks_metadata(monkeypatch: pytest.MonkeyPatch):
    mock_api = _reload_offline_mock_api(monkeypatch)
    mock_api.reset_mock_tasks()

    result_payload = {"analysis": {"findings": [{"title": "t"}], "compliance_score": 90}}
    task = mock_api._store_completed_task(
        task_id="123", filename="file.txt", result=result_payload, user=mock_api.get_current_active_user()
    )

    assert task["status"] == "completed"
    assert task["findings"] == [{"title": "t"}]
    assert task["overall_score"] == 90
    assert mock_api._tasks["123"]["result"] is task["result"]
    assert mock_api._tasks["123"]["result"] is not result_payload


def test_offline_client_post_and_get(monkeypatch: pytest.MonkeyPatch):
    mock_api = _reload_offline_mock_api(monkeypatch)
    mock_api.reset_mock_tasks()

    with mock_api.create_offline_test_client() as client:
        response = asyncio.run(
            client.post(
                "/analysis/analyze",
                files={"file": ("sample.txt", io.BytesIO(b"hello"), "text/plain")},
                data={"discipline": "ot", "analysis_mode": "rubric"},
            )
        )

        assert response.status_code == 202
        task_id = response.json()["task_id"]

        status_response = client.get(f"/analysis/status/{task_id}")
        assert status_response.status_code == 200
        payload = status_response.json()
        assert payload["task_id"] == task_id
        assert payload["status"] == "completed"


def test_offline_client_handles_inactive_user(monkeypatch: pytest.MonkeyPatch):
    mock_api = _reload_offline_mock_api(monkeypatch)

    inactive_user = types.SimpleNamespace(id=2, username="inactive", is_active=False, is_admin=False)

    with mock_api.create_offline_test_client(user=inactive_user) as client:
        response = asyncio.run(
            client.post(
                "/analysis/analyze",
                files={"file": ("sample.txt", io.BytesIO(b""), "text/plain")},
                data={"discipline": "pt", "analysis_mode": "rubric"},
            )
        )

        assert response.status_code == 403

        missing_response = client.get("/analysis/status/missing")
        assert missing_response.status_code == 403
