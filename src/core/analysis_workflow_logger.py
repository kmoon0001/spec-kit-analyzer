"""Analysis Workflow Logger - Comprehensive logging for analysis workflow debugging.
import requests

This module provides detailed logging capabilities to track each step of the
document analysis process, helping identify where workflows fail or hang.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any


class AnalysisWorkflowLogger:
    """Comprehensive logger for analysis workflow debugging.

    Tracks all steps of the analysis process including:
    - Analysis initiation
    - API requests and responses
    - Polling attempts
    - Workflow completion/failure
    """

    def __init__(self, logger_name: str = "analysis_workflow"):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)

        # Create formatter for detailed logging
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Add console handler if not already present
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # Track current analysis session
        self.current_session: dict[str, Any] | None = None
        self.session_start_time: float | None = None

    def log_analysis_start(self, file_path: str, rubric: str, user_id: str = "unknown") -> str:
        """Log the start of an analysis workflow.

        Args:
            file_path: Path to the document being analyzed
            rubric: Selected compliance rubric
            user_id: ID of the user initiating analysis

        Returns:
            Session ID for tracking this analysis

        """
        session_id = f"analysis_{int(time.time())}"
        self.session_start_time = time.time()

        self.current_session = {
            "session_id": session_id,
            "file_path": file_path,
            "file_name": Path(file_path).name,
            "file_size": self._get_file_size(file_path),
            "rubric": rubric,
            "user_id": user_id,
            "start_time": datetime.now().isoformat(),
            "steps": [],
        }

        self.logger.info(
            "🚀 ANALYSIS STARTED - Session: %s | File: %s (%s bytes) | Rubric: %s | User: %s",
            session_id,
            Path(file_path).name,
            len(Path(file_path).read_bytes()) if Path(file_path).exists() else 0,
            rubric,
            user_id)

        return session_id

    def log_api_request(self, endpoint: str, method: str = "POST", payload: dict | None = None) -> None:
        """Log API request details.

        Args:
            endpoint: API endpoint being called
            method: HTTP method (GET, POST, etc.)
            payload: Request payload (sensitive data will be sanitized)

        """
        if not self.current_session:
            self.logger.warning("API request logged without active session")
            return

        # Sanitize payload for logging (remove sensitive data)
        safe_payload = self._sanitize_payload(payload) if payload else None

        step = {
            "step": "api_request",
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "payload_size": len(str(payload)) if payload else 0,
        }

        self.current_session["steps"].append(step)

        self.logger.info(
            "📤 API REQUEST - %s %s | Payload size: %s chars | %s",
            method,
            endpoint,
            step["payload_size"],
            f"Session: {self.current_session['session_id']}")

        if safe_payload:
            self.logger.debug("Request payload: %s", safe_payload)

    def log_api_response(self, status_code: int, response: dict | None = None, error: str | None = None) -> None:
        """Log API response details.

        Args:
            status_code: HTTP status code
            response: Response data
            error: Error message if request failed

        """
        if not self.current_session:
            self.logger.warning("API response logged without active session")
            return

        step = {
            "step": "api_response",
            "timestamp": datetime.now().isoformat(),
            "status_code": status_code,
            "success": 200 <= status_code < 300,
            "response_size": len(str(response)) if response else 0,
            "error": error,
        }

        self.current_session["steps"].append(step)

        if step["success"]:
            self.logger.info(
                "✅ API RESPONSE - Status: %s | Response size: %s chars | ",
                status_code,
                step["response_size"],
                f"Session: {self.current_session['session_id']}")

            # Log task ID if present
            if response and "task_id" in response:
                self.logger.info("📋 Task ID received: %s", response["task_id"])
        else:
            self.logger.error(
                "❌ API ERROR - Status: %s | Error: %s | ",
                status_code,
                error,
                f"Session: {self.current_session['session_id']}")

    def log_polling_attempt(
        self, task_id: str, attempt: int, status: str | None = None, progress: int | None = None
    ) -> None:
        """Log polling attempt for analysis status.

        Args:
            task_id: Analysis task ID being polled
            attempt: Polling attempt number
            status: Current analysis status
            progress: Analysis progress percentage

        """
        if not self.current_session:
            self.logger.warning("Polling attempt logged without active session")
            return

        step = {
            "step": "polling_attempt",
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "attempt": attempt,
            "status": status,
            "progress": progress,
        }

        self.current_session["steps"].append(step)

        elapsed = time.time() - self.session_start_time if self.session_start_time else 0

        self.logger.info(
            "🔄 POLLING ATTEMPT #%s - Task: {task_id[:8]}... | Status: %s | Progress: {progress}% | ",
            attempt,
            status,
            f"Elapsed: {elapsed}s | Session: {self.current_session['session_id']}")

    def log_workflow_completion(self, success: bool, result: dict | None = None, error: str | None = None) -> None:
        """Log workflow completion or failure.

        Args:
            success: Whether the workflow completed successfully
            result: Analysis result data
            error: Error message if workflow failed

        """
        if not self.current_session:
            self.logger.warning("Workflow completion logged without active session")
            return

        duration = time.time() - self.session_start_time if self.session_start_time else 0

        step = {
            "step": "workflow_completion",
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "duration": duration,
            "result_size": len(str(result)) if result else 0,
            "error": error,
        }

        self.current_session["steps"].append(step)

        if success:
            self.logger.info(
                "🎉 ANALYSIS COMPLETED - Duration: %ss | Result size: %s chars | ",
                duration,
                step["result_size"],
                f"Session: {self.current_session['session_id']}")
        else:
            self.logger.error(
                "💥 ANALYSIS FAILED - Duration: %ss | Error: %s | ",
                duration,
                error,
                f"Session: {self.current_session['session_id']}")

        # Log session summary
        self._log_session_summary()

    def log_workflow_timeout(self, timeout_seconds: float) -> None:
        """Log workflow timeout.

        Args:
            timeout_seconds: Timeout threshold that was exceeded

        """
        if not self.current_session:
            self.logger.warning("Workflow timeout logged without active session")
            return

        duration = time.time() - self.session_start_time if self.session_start_time else 0

        self.logger.error(
            "⏰ ANALYSIS TIMEOUT - Duration: %ss | Timeout threshold: %ss | ",
            duration,
            timeout_seconds,
            f"Session: {self.current_session['session_id']}")

        self._log_session_summary()

    def get_current_session(self) -> dict[str, Any] | None:
        """Get current analysis session data."""
        return self.current_session.copy() if self.current_session else None

    def reset_session(self) -> None:
        """Reset current analysis session."""
        if self.current_session:
            self.logger.debug("Resetting session: %s", self.current_session["session_id"])

        self.current_session = None
        self.session_start_time = None

    def _get_file_size(self, file_path: str) -> int:
        """Get file size safely."""
        try:
            return Path(file_path).stat().st_size
        except (PermissionError, OSError, FileNotFoundError):
            return 0

    def _sanitize_payload(self, payload: dict) -> dict:
        """Remove sensitive data from payload for logging."""
        if not payload:
            return {}

        # Create a copy and remove sensitive fields
        safe_payload = payload.copy()

        # Remove or mask sensitive fields
        sensitive_fields = ["password", "token", "key", "secret", "auth"]
        for field in sensitive_fields:
            if field in safe_payload:
                safe_payload[field] = "***REDACTED***"

        # Truncate large text fields
        if "content" in safe_payload and len(str(safe_payload["content"])) > 200:
            safe_payload["content"] = str(safe_payload["content"])[:200] + "...[truncated]"

        return safe_payload

    def _log_session_summary(self) -> None:
        """Log a summary of the current session."""
        if not self.current_session:
            return

        session = self.current_session
        step_counts: dict[str, int] = {}

        # Count step types
        for step in session["steps"]:
            step_type = step["step"]
            step_counts[step_type] = step_counts.get(step_type, 0) + 1

        duration = time.time() - self.session_start_time if self.session_start_time else 0

        self.logger.info(
            "📊 SESSION SUMMARY - %s | File: %s | Duration: {duration}s | ",
            session["session_id"],
            session["file_name"],
            f"Steps: {step_counts}")


# Global logger instance
# Global logger instance
# Global logger instance
workflow_logger = AnalysisWorkflowLogger()
