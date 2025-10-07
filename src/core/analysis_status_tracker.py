"""
Analysis Status Tracker - Monitor analysis progress and detect hanging processes.

This module provides status tracking capabilities to monitor analysis progress,
detect timeouts, and trigger recovery mechanisms when analyses hang or fail.
"""

import time
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AnalysisState(Enum):
    """Analysis workflow states."""
    IDLE = "idle"
    STARTING = "starting"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    POLLING = "polling"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class AnalysisStatusTracker:
    """
    Track analysis progress and detect hanging processes.
    
    Monitors analysis workflow state, progress, and timing to detect
    issues like timeouts, hanging processes, and communication failures.
    """
    
    def __init__(self, timeout_threshold: float = 120.0):
        """
        Initialize the status tracker.
        
        Args:
            timeout_threshold: Timeout threshold in seconds (default: 2 minutes)
        """
        self.timeout_threshold = timeout_threshold
        self.reset()
        
        # Callbacks for status changes
        self._status_callbacks: Dict[AnalysisState, list] = {}
        self._timeout_callbacks: list = []
    
    def reset(self) -> None:
        """Reset tracker to idle state."""
        self.current_analysis: Optional[str] = None
        self.task_id: Optional[str] = None
        self.state = AnalysisState.IDLE
        self.start_time: Optional[float] = None
        self.last_update: Optional[float] = None
        self.progress: int = 0
        self.status_message: str = ""
        self.error_message: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
        
        logger.debug("Analysis status tracker reset to idle state")
    
    def start_tracking(self, analysis_id: str, file_path: str, rubric: str) -> None:
        """
        Start tracking a new analysis.
        
        Args:
            analysis_id: Unique identifier for this analysis
            file_path: Path to the document being analyzed
            rubric: Selected compliance rubric
        """
        self.reset()
        
        self.current_analysis = analysis_id
        self.state = AnalysisState.STARTING
        self.start_time = time.time()
        self.last_update = self.start_time
        self.progress = 0
        self.status_message = "Starting analysis..."
        
        self.metadata = {
            "file_path": file_path,
            "rubric": rubric,
            "started_at": datetime.now().isoformat()
        }
        
        logger.info(f"Started tracking analysis: {analysis_id}")
        self._trigger_status_callback(AnalysisState.STARTING)
    
    def update_status(self, state: AnalysisState, progress: int = None, 
                     message: str = None, task_id: str = None) -> None:
        """
        Update analysis status.
        
        Args:
            state: New analysis state
            progress: Progress percentage (0-100)
            message: Status message
            task_id: Analysis task ID (if available)
        """
        if not self.current_analysis:
            logger.warning("Status update attempted without active analysis")
            return
        
        old_state = self.state
        self.state = state
        self.last_update = time.time()
        
        if progress is not None:
            self.progress = max(0, min(100, progress))
        
        if message is not None:
            self.status_message = message
        
        if task_id is not None:
            self.task_id = task_id
        
        # Log significant state changes
        if old_state != state:
            elapsed = self.get_elapsed_time()
            logger.info(
                f"Analysis state changed: {old_state.value} → {state.value} | "
                f"Progress: {self.progress}% | Elapsed: {elapsed:.1f}s | "
                f"Analysis: {self.current_analysis}"
            )
            self._trigger_status_callback(state)
        
        # Check for timeout
        if self.check_timeout():
            self._handle_timeout()
    
    def set_task_id(self, task_id: str) -> None:
        """Set the analysis task ID."""
        self.task_id = task_id
        logger.debug(f"Task ID set: {task_id} for analysis: {self.current_analysis}")
    
    def set_error(self, error_message: str) -> None:
        """
        Set error state with message.
        
        Args:
            error_message: Error description
        """
        self.state = AnalysisState.FAILED
        self.error_message = error_message
        self.last_update = time.time()
        
        elapsed = self.get_elapsed_time()
        logger.error(
            f"Analysis failed: {error_message} | "
            f"Elapsed: {elapsed:.1f}s | Analysis: {self.current_analysis}"
        )
        
        self._trigger_status_callback(AnalysisState.FAILED)
    
    def complete_analysis(self, result_data: Optional[Dict] = None) -> None:
        """
        Mark analysis as completed.
        
        Args:
            result_data: Analysis result data
        """
        if not self.current_analysis:
            logger.warning("Completion attempted without active analysis")
            return
        
        self.state = AnalysisState.COMPLETED
        self.progress = 100
        self.status_message = "Analysis completed successfully"
        self.last_update = time.time()
        
        if result_data:
            self.metadata["result"] = result_data
        
        elapsed = self.get_elapsed_time()
        logger.info(
            f"Analysis completed successfully | "
            f"Duration: {elapsed:.1f}s | Analysis: {self.current_analysis}"
        )
        
        self._trigger_status_callback(AnalysisState.COMPLETED)
    
    def cancel_analysis(self) -> None:
        """Cancel the current analysis."""
        if not self.current_analysis:
            logger.warning("Cancellation attempted without active analysis")
            return
        
        self.state = AnalysisState.CANCELLED
        self.status_message = "Analysis cancelled by user"
        self.last_update = time.time()
        
        elapsed = self.get_elapsed_time()
        logger.info(
            f"Analysis cancelled by user | "
            f"Elapsed: {elapsed:.1f}s | Analysis: {self.current_analysis}"
        )
        
        self._trigger_status_callback(AnalysisState.CANCELLED)
    
    def check_timeout(self) -> bool:
        """
        Check if analysis has timed out.
        
        Returns:
            True if analysis has exceeded timeout threshold
        """
        if not self.current_analysis or not self.last_update:
            return False
        
        if self.state in [AnalysisState.COMPLETED, AnalysisState.FAILED, 
                         AnalysisState.CANCELLED, AnalysisState.TIMEOUT]:
            return False
        
        elapsed_since_update = time.time() - self.last_update
        return elapsed_since_update > self.timeout_threshold
    
    def get_elapsed_time(self) -> float:
        """Get total elapsed time since analysis started."""
        if not self.start_time:
            return 0.0
        return time.time() - self.start_time
    
    def get_time_since_update(self) -> float:
        """Get time since last status update."""
        if not self.last_update:
            return 0.0
        return time.time() - self.last_update
    
    def is_active(self) -> bool:
        """Check if analysis is currently active."""
        return self.state not in [
            AnalysisState.IDLE, AnalysisState.COMPLETED, 
            AnalysisState.FAILED, AnalysisState.CANCELLED, AnalysisState.TIMEOUT
        ]
    
    def is_stuck(self) -> bool:
        """
        Check if analysis appears to be stuck.
        
        Returns:
            True if analysis has been in the same state too long
        """
        if not self.is_active():
            return False
        
        # Consider stuck if no updates for half the timeout threshold
        stuck_threshold = self.timeout_threshold / 2
        return self.get_time_since_update() > stuck_threshold
    
    def get_status_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive status summary.
        
        Returns:
            Dictionary with current status information
        """
        return {
            "analysis_id": self.current_analysis,
            "task_id": self.task_id,
            "state": self.state.value,
            "progress": self.progress,
            "status_message": self.status_message,
            "error_message": self.error_message,
            "elapsed_time": self.get_elapsed_time(),
            "time_since_update": self.get_time_since_update(),
            "is_active": self.is_active(),
            "is_stuck": self.is_stuck(),
            "timeout_threshold": self.timeout_threshold,
            "metadata": self.metadata.copy()
        }
    
    def add_status_callback(self, state: AnalysisState, callback: Callable) -> None:
        """
        Add callback for specific state changes.
        
        Args:
            state: State to monitor
            callback: Function to call when state is reached
        """
        if state not in self._status_callbacks:
            self._status_callbacks[state] = []
        self._status_callbacks[state].append(callback)
    
    def add_timeout_callback(self, callback: Callable) -> None:
        """
        Add callback for timeout events.
        
        Args:
            callback: Function to call when timeout occurs
        """
        self._timeout_callbacks.append(callback)
    
    def _trigger_status_callback(self, state: AnalysisState) -> None:
        """Trigger callbacks for state change."""
        if state in self._status_callbacks:
            for callback in self._status_callbacks[state]:
                try:
                    callback(self.get_status_summary())
                except Exception as e:
                    logger.error(f"Error in status callback: {e}")
    
    def _handle_timeout(self) -> None:
        """Handle analysis timeout."""
        if self.state == AnalysisState.TIMEOUT:
            return  # Already handled
        
        self.state = AnalysisState.TIMEOUT
        self.status_message = f"Analysis timed out after {self.timeout_threshold}s"
        self.last_update = time.time()
        
        elapsed = self.get_elapsed_time()
        logger.error(
            f"Analysis timed out | "
            f"Elapsed: {elapsed:.1f}s | Threshold: {self.timeout_threshold}s | "
            f"Analysis: {self.current_analysis}"
        )
        
        # Trigger timeout callbacks
        for callback in self._timeout_callbacks:
            try:
                callback(self.get_status_summary())
            except Exception as e:
                logger.error(f"Error in timeout callback: {e}")
        
        self._trigger_status_callback(AnalysisState.TIMEOUT)


# Global status tracker instance
status_tracker = AnalysisStatusTracker()