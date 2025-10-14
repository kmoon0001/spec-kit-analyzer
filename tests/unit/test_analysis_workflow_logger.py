import logging
from pathlib import Path

import pytest

from src.core.analysis_workflow_logger import AnalysisWorkflowLogger


@pytest.fixture()
def temp_logger() -> AnalysisWorkflowLogger:
    name = f"test_logger_{id(object())}"
    logger = AnalysisWorkflowLogger(name)
    yield logger
    logger.reset_session()


def test_log_analysis_start_records_session_metadata(temp_logger: AnalysisWorkflowLogger, tmp_path: Path) -> None:
    file_path = tmp_path / "document.txt"
    file_path.write_text("clinical note", encoding="utf-8")

    session_id = temp_logger.log_analysis_start(str(file_path), rubric="default")
    session = temp_logger.get_current_session()

    assert session is not None
    assert session["session_id"] == session_id
    assert session["file_name"] == file_path.name
    assert session["file_size"] == file_path.stat().st_size
    assert session["steps"] == []


def test_log_api_request_sanitises_payload(temp_logger: AnalysisWorkflowLogger, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    dummy_file = tmp_path / "note.txt"
    dummy_file.write_text("note", encoding="utf-8")
    temp_logger.log_analysis_start(str(dummy_file), rubric="default")

    caplog.set_level(logging.DEBUG)
    temp_logger.log_api_request(
        endpoint="/analysis/start",
        method="POST",
        payload={"token": "secret-value", "notes": "x" * 250},
    )

    payload_logs = [record.message for record in caplog.records if "API request payload" in record.message]
    assert payload_logs, "Expected sanitised payload log entry"

    payload_entry = payload_logs[-1]
    assert "***REDACTED***" in payload_entry
    assert "secret-value" not in payload_entry
    assert "[truncated]" in payload_entry


def test_log_workflow_timeout_appends_step(temp_logger: AnalysisWorkflowLogger, tmp_path: Path) -> None:
    dummy_file = tmp_path / "report.txt"
    dummy_file.write_text("data", encoding="utf-8")
    temp_logger.log_analysis_start(str(dummy_file), rubric="default")

    temp_logger.log_workflow_timeout(timeout_seconds=120.0)
    session = temp_logger.get_current_session()
    assert session is not None

    timeout_steps = [step for step in session["steps"] if step.get("step") == "workflow_timeout"]
    assert len(timeout_steps) == 1
    assert timeout_steps[0]["timeout_threshold"] == pytest.approx(120.0)
    assert timeout_steps[0]["duration"] >= 0.0
