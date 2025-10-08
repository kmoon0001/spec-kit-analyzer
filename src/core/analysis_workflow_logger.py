"""
Analysis Workflow Logger - Comprehensive logging for analysis workflow debugging.

This module provides detailed logging capabilities to track each step of the 
document analysis process, helping identify where workflows fail or hang.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path


class AnalysisWorkflowLogger:
    """
    Comprehensive logger for analysis workflow debugging.
    
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
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Add console handler if not already present
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # Track current analysis session
        self.current_session: Optional[Dict[str, Any]] = None
        self.session_start_time: Optional[float] = None
    
    def log_analysis_start(self, file_path: str, rubric: str, user_id: str = "unknown") -> str:
        """
        Log the start of an analysis workflow.
        
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
            "steps": []
        }
        
        self.logger.info(
            f"🚀 ANALYSIS STARTED - Session: {session_id} | "
            f"File: {Path(file_path).name} ({self.current_session['file_size']} bytes) | "
            f"Rubric: {rubric} | User: {user_id}"
        )
        
        return session_id
    
    def log_api_request(self, endpoint: str, method: str = "POST", payload: Optional[Dict] = None) -> None:
        """
        Log API request details.
        
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
            "payload_size": len(str(payload)) if payload else 0
        }
        
        self.current_session["steps"].append(step)
        
        self.logger.info(
            f"📤 API REQUEST - {method} {endpoint} | "
            f"Payload size: {step['payload_size']} chars | "
            f"Session: {self.current_session['session_id']}"
        )
        
        if safe_payload:
            self.logger.debug(f"Request payload: {safe_payload}")
    
    def log_api_response(self, status_code: int, response: Optional[Dict] = None, 
                        error: Optional[str] = None) -> None:
        """
        Log API response details.
        
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
            "error": error
        }
        
        self.current_session["steps"].append(step)
        
        if step["success"]:
            self.logger.info(
                f"✅ API RESPONSE - Status: {status_code} | "
                f"Response size: {step['response_size']} chars | "
                f"Session: {self.current_session['session_id']}"
            )
            
            # Log task ID if present
            if response and "task_id" in response:
                self.logger.info(f"📋 Task ID received: {response['task_id']}")
        else:
            self.logger.error(
                f"❌ API ERROR - Status: {status_code} | "
                f"Error: {error} | "
                f"Session: {self.current_session['session_id']}"
            )
    
    def log_polling_attempt(self, task_id: str, attempt: int, status: Optional[str] = None,
                           progress: Optional[int] = None) -> None:
        """
        Log polling attempt for analysis status.
        
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
            "progress": progress
        }
        
        self.current_session["steps"].append(step)
        
        elapsed = time.time() - self.session_start_time if self.session_start_time else 0
        
        self.logger.info(
            f"🔄 POLLING ATTEMPT #{attempt} - Task: {task_id[:8]}... | "
            f"Status: {status} | Progress: {progress}% | "
            f"Elapsed: {elapsed:.1f}s | Session: {self.current_session['session_id']}"
        )
    
    def log_workflow_completion(self, success: bool, result: Optional[Dict] = None,
                               error: Optional[str] = None) -> None:
        """
        Log workflow completion or failure.
        
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
            "error": error
        }
        
        self.current_session["steps"].append(step)
        
        if success:
            self.logger.info(
                f"🎉 ANALYSIS COMPLETED - Duration: {duration:.1f}s | "
                f"Result size: {step['result_size']} chars | "
                f"Session: {self.current_session['session_id']}"
            )
        else:
            self.logger.error(
                f"💥 ANALYSIS FAILED - Duration: {duration:.1f}s | "
                f"Error: {error} | "
                f"Session: {self.current_session['session_id']}"
            )
        
        # Log session summary
        self._log_session_summary()
    
    def log_workflow_timeout(self, timeout_seconds: float) -> None:
        """
        Log workflow timeout.
        
        Args:
            timeout_seconds: Timeout threshold that was exceeded
        """
        if not self.current_session:
            self.logger.warning("Workflow timeout logged without active session")
            return
        
        duration = time.time() - self.session_start_time if self.session_start_time else 0
        
        self.logger.error(
            f"⏰ ANALYSIS TIMEOUT - Duration: {duration:.1f}s | "
            f"Timeout threshold: {timeout_seconds}s | "
            f"Session: {self.current_session['session_id']}"
        )
        
        self._log_session_summary()
    
    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """Get current analysis session data."""
        return self.current_session.copy() if self.current_session else None
    
    def reset_session(self) -> None:
        """Reset current analysis session."""
        if self.current_session:
            self.logger.debug(f"Resetting session: {self.current_session['session_id']}")
        
        self.current_session = None
        self.session_start_time = None
    
    def _get_file_size(self, file_path: str) -> int:
        """Get file size safely."""
        try:
            return Path(file_path).stat().st_size
        except Exception:
            return 0
    
    def _sanitize_payload(self, payload: Dict) -> Dict:
        """Remove sensitive data from payload for logging."""
        if not payload:
            return {}
        
        # Create a copy and remove sensitive fields
        safe_payload = payload.copy()
        
        # Remove or mask sensitive fields
        sensitive_fields = ['password', 'token', 'key', 'secret', 'auth']
        for field in sensitive_fields:
            if field in safe_payload:
                safe_payload[field] = "***REDACTED***"
        
        # Truncate large text fields
        if 'content' in safe_payload and len(str(safe_payload['content'])) > 200:
            safe_payload['content'] = str(safe_payload['content'])[:200] + "...[truncated]"
        
        return safe_payload
    
    def _log_session_summary(self) -> None:
        """Log a summary of the current session."""
        if not self.current_session:
            return
        
        session = self.current_session
        step_counts: Dict[str, int] = {}
        
        # Count step types
        for step in session["steps"]:
            step_type = step["step"]
            step_counts[step_type] = step_counts.get(step_type, 0) + 1
        
        duration = time.time() - self.session_start_time if self.session_start_time else 0
        
        self.logger.info(
            f"📊 SESSION SUMMARY - {session['session_id']} | "
            f"File: {session['file_name']} | Duration: {duration:.1f}s | "
            f"Steps: {step_counts}"
        )


# Global logger instance
workflow_logger = AnalysisWorkflowLogger()
