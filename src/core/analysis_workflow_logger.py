"""Structured logging utilities for the document analysis workflow.

This module centralises logging around the analysis workflow so engineers can
trace every significant step when diagnosing hanging or failed analyses.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Final


_LOGGER_NAME: Final[str] = "analysis_workflow"
_SENSITIVE_KEYS: Final[set[str]] = {"password", "token", "key", "secret", "auth"}
_MAX_TEXT_LENGTH: Final[int] = 200


@dataclass(slots=True)
class _SessionData:
    """Container for the in-flight analysis session."""

    session_id: str
    file_path: str
    file_name: str
    file_size: int
    rubric: str
    user_id: str
    iso_started_at: str
    steps: list[dict[str, Any]] = field(default_factory=list)


class AnalysisWorkflowLogger:
    """Comprehensive logger for tracking the analysis workflow lifecycle."""

    def __init__(self, logger_name: str = _LOGGER_NAME) -> None:
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)

        # Ensure the logger always has at least a NullHandler so library usage
        # does not emit "No handler could be found" warnings.
        if not self.logger.handlers:
            self.logger.addHandler(logging.NullHandler())

        self._session: _SessionData | None = None
        self._started_monotonic: float | None = None

    # ------------------------------------------------------------------
    # Session lifecycle helpers
    # ------------------------------------------------------------------
    def log_analysis_start(self, file_path: str, rubric: str, user_id: str = "unknown") -> str:
        """Log the start of an analysis workflow and create a tracking session."""
        session_id = f"analysis_{int(time.time() * 1000)}"
        started_monotonic = time.perf_counter()
        file_info = Path(file_path)
        file_name = file_info.name
        file_size = self._safe_file_size(file_info)

        self._session = _SessionData(
            session_id=session_id,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            rubric=rubric,
            user_id=user_id,
            iso_started_at=self._now_iso(),
        )
        self._started_monotonic = started_monotonic

        self.logger.info(
            "Analysis started | session=%s | file=%s | size_bytes=%s | rubric=%s | user=%s",
            session_id,
            file_name,
            file_size,
            rubric,
            user_id,
        )

        return session_id

    def log_api_request(self, endpoint: str, method: str = "POST", payload: dict | None = None) -> None:
        """Log outbound API request metadata."""
        session = self._require_session("API request")
        if not session:
            return

        safe_payload = self._sanitize_payload(payload) if payload else None
        payload_size = len(str(payload)) if payload is not None else 0

        step = {
            "step": "api_request",
            "timestamp": self._now_iso(),
            "endpoint": endpoint,
            "method": method,
            "payload_size": payload_size,
        }
        session.steps.append(step)

        self.logger.info(
            "API request | session=%s | method=%s | endpoint=%s | payload_size=%s",
            session.session_id,
            method,
            endpoint,
            payload_size,
        )
        if safe_payload:
            self.logger.debug("API request payload | session=%s | payload=%s", session.session_id, safe_payload)

    def log_api_response(self, status_code: int, response: dict | None = None, error: str | None = None) -> None:
        """Log API response metadata and outcome."""
        session = self._require_session("API response")
        if not session:
            return

        success = 200 <= status_code < 300
        response_size = len(str(response)) if response is not None else 0
        truncated_error = self._truncate_text(error) if error else None

        step = {
            "step": "api_response",
            "timestamp": self._now_iso(),
            "status_code": status_code,
            "success": success,
            "response_size": response_size,
            "error": truncated_error,
        }
        session.steps.append(step)

        if success:
            self.logger.info(
                "API response | session=%s | status=%s | response_size=%s",
                session.session_id,
                status_code,
                response_size,
            )
        else:
            self.logger.error(
                "API error | session=%s | status=%s | error=%s",
                session.session_id,
                status_code,
                truncated_error,
            )

        if response and "task_id" in response:
            self.logger.info(
                "Task identifier received | session=%s | task_id=%s", session.session_id, response["task_id"]
            )

    def log_polling_attempt(
        self,
        task_id: str,
        attempt: int,
        status: str | None = None,
        progress: int | None = None,
    ) -> None:
        """Log a polling attempt while monitoring an analysis task."""
        session = self._require_session("Polling attempt")
        if not session:
            return

        elapsed = self._elapsed_seconds()
        step = {
            "step": "polling_attempt",
            "timestamp": self._now_iso(),
            "task_id": task_id,
            "attempt": attempt,
            "status": status,
            "progress": progress,
            "elapsed": elapsed,
        }
        session.steps.append(step)

        self.logger.info(
            "Polling attempt | session=%s | task=%s | attempt=%s | status=%s | progress=%s | elapsed=%.2fs",
            session.session_id,
            task_id,
            attempt,
            status or "unknown",
            "?" if progress is None else progress,
            elapsed,
        )

    def log_workflow_completion(self, success: bool, result: dict | None = None, error: str | None = None) -> None:
        """Log workflow completion, whether successful or not."""
        session = self._require_session("Workflow completion")
        if not session:
            return

        duration = self._elapsed_seconds()
        result_size = len(str(result)) if result is not None else 0
        truncated_error = self._truncate_text(error) if error else None

        step = {
            "step": "workflow_completion",
            "timestamp": self._now_iso(),
            "success": success,
            "duration": duration,
            "result_size": result_size,
            "error": truncated_error,
        }
        session.steps.append(step)

        if success:
            self.logger.info(
                "Analysis completed | session=%s | duration=%.2fs | result_size=%s",
                session.session_id,
                duration,
                result_size,
            )
        else:
            self.logger.error(
                "Analysis failed | session=%s | duration=%.2fs | error=%s",
                session.session_id,
                duration,
                truncated_error,
            )

        self._log_session_summary()

    def log_workflow_timeout(self, timeout_seconds: float) -> None:
        """Log when the workflow exceeds the configured timeout threshold."""
        session = self._require_session("Workflow timeout")
        if not session:
            return

        duration = self._elapsed_seconds()
        step = {
            "step": "workflow_timeout",
            "timestamp": self._now_iso(),
            "timeout_threshold": timeout_seconds,
            "duration": duration,
        }
        session.steps.append(step)

        self.logger.error(
            "Analysis timeout | session=%s | duration=%.2fs | timeout_threshold=%.2fs",
            session.session_id,
            duration,
            timeout_seconds,
        )

        self._log_session_summary()

    # ------------------------------------------------------------------
    # Session inspection helpers
    # ------------------------------------------------------------------
    def get_current_session(self) -> dict[str, Any] | None:
        """Return a shallow copy of the current session data."""
        if not self._session:
            return None
        return {
            "session_id": self._session.session_id,
            "file_path": self._session.file_path,
            "file_name": self._session.file_name,
            "file_size": self._session.file_size,
            "rubric": self._session.rubric,
            "user_id": self._session.user_id,
            "started_at": self._session.iso_started_at,
            "steps": [step.copy() for step in self._session.steps],
        }

    def reset_session(self) -> None:
        """Clear the current session state."""
        if self._session:
            self.logger.debug("Resetting session | session=%s", self._session.session_id)
        self._session = None
        self._started_monotonic = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _require_session(self, context: str) -> _SessionData | None:
        if not self._session:
            self.logger.warning("%s logged without an active session", context)
            return None
        return self._session

    def _elapsed_seconds(self) -> float:
        if self._started_monotonic is None:
            return 0.0
        return max(0.0, time.perf_counter() - self._started_monotonic)

    @staticmethod
    def _safe_file_size(path: Path) -> int:
        try:
            return path.stat().st_size
        except (FileNotFoundError, OSError, PermissionError):
            return 0

    @staticmethod
    def _sanitize_payload(payload: dict) -> dict:
        safe_payload = {}
        for key, value in payload.items():
            key_lower = key.lower()
            if key_lower in _SENSITIVE_KEYS:
                safe_payload[key] = "***REDACTED***"
                continue

            safe_payload[key] = AnalysisWorkflowLogger._truncate_text(value)
        return safe_payload

    @staticmethod
    def _truncate_text(value: Any) -> Any:
        if isinstance(value, str) and len(value) > _MAX_TEXT_LENGTH:
            return f"{value[:_MAX_TEXT_LENGTH]}...[truncated]"
        return value

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(UTC).isoformat()

    def _log_session_summary(self) -> None:
        session = self._session
        if not session:
            return

        step_counts: dict[str, int] = {}
        for step in session.steps:
            name = step.get("step", "unknown")
            step_counts[name] = step_counts.get(name, 0) + 1

        duration = self._elapsed_seconds()
        self.logger.info(
            "Session summary | session=%s | file=%s | duration=%.2fs | steps=%s",
            session.session_id,
            session.file_name,
            duration,
            step_counts,
        )


# Global singleton used throughout the PySide application.
workflow_logger = AnalysisWorkflowLogger()
