"""
Base Worker Class for All Background Operations

Provides a robust foundation for all worker threads with:
    - Automatic exception handling
    - Timeout management
    - Resource checking before execution
    - Progress reporting
    - Cancellation support
    - Secure cleanup

All workers should inherit from BaseWorker to ensure consistent,
safe behavior across the application.
"""

import time
import traceback
import logging
from abc import ABCMeta, abstractmethod
from typing import Any, Optional
from PySide6.QtCore import QRunnable, Slot

from .worker_signals import WorkerSignals
from .resource_monitor import ResourceMonitor


logger = logging.getLogger(__name__)


class ABCQRunnable(ABCMeta, type(QRunnable)):
    """Metaclass that combines ABC and QRunnable."""
    pass


class BaseWorker(QRunnable, metaclass=ABCQRunnable):
    """
    Abstract base class for all worker threads.
    
    Provides:
        - Signal-based communication with GUI
        - Exception handling and error reporting
        - Timeout enforcement
        - Resource checking
        - Cancellation support
        - Automatic cleanup
    
    Usage:
        class MyWorker(BaseWorker):
            def __init__(self, data):
                super().__init__()
                self.data = data
            
            def do_work(self) -> Any:
                # Your actual work here
                result = process(self.data)
                return result
    
    The worker will:
        - Check resources before starting
        - Handle all exceptions
        - Enforce timeout
        - Report progress
        - Clean up automatically
    """
    
    def __init__(
        self,
        timeout_seconds: float = 300.0,
        resource_monitor: Optional[ResourceMonitor] = None,
        job_type: str = "general"
    ):
        """
        Initialize base worker.
        
        Args:
            timeout_seconds: Maximum execution time (0 = no timeout)
            resource_monitor: Resource monitor instance (creates new if None)
            job_type: Type of job for resource checking
        """
        super().__init__()
        
        # Configuration
        self.timeout_seconds = timeout_seconds
        self.job_type = job_type
        self.resource_monitor = resource_monitor or ResourceMonitor()
        
        # State
        self._is_cancelled = False
        self._start_time: Optional[float] = None
        self._result: Any = None
        
        # Signals must be created here (not in run())
        self.signals = self.create_signals()
        
        # Auto-delete after completion
        self.setAutoDelete(True)
    
    @abstractmethod
    def create_signals(self) -> WorkerSignals:
        """
        Create signal object for this worker.
        
        Override to use specialized signal classes:
            def create_signals(self):
                return AnalysisSignals()
        
        Returns:
            WorkerSignals or subclass instance
        """
        return WorkerSignals()
    
    @abstractmethod
    def do_work(self) -> Any:
        """
        Perform the actual work.
        
        This method runs in the worker thread. It should:
            - Perform the computation/I/O
            - Check self.is_cancelled() periodically
            - Call self.report_progress() to update UI
            - Return the result
            - Raise exceptions on errors
        
        Returns:
            Result data (will be emitted via result signal)
            
        Raises:
            Any exception (will be caught and emitted via error signal)
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """
        Clean up resources after work completes.
        
        Called automatically after do_work() finishes (success or failure).
        Override to:
            - Delete temp files securely
            - Free memory
            - Close connections
            - Reset state
        """
        pass
    
    @Slot()
    def run(self):
        """
        Main execution method (called by QThreadPool).
        
        DO NOT OVERRIDE - This handles all the safety logic.
        Override do_work() instead.
        """
        self._start_time = time.time()
        
        try:
            # Emit started signal
            self.signals.started.emit()
            logger.debug(f"{self.__class__.__name__} started")
            
            # Check if cancelled before starting
            if self._is_cancelled:
                logger.info(f"{self.__class__.__name__} cancelled before start")
                self.signals.cancelled.emit()
                return
            
            # Check resources
            can_start, reason = self.resource_monitor.can_start_job(self.job_type)
            if not can_start:
                logger.warning(f"{self.__class__.__name__} denied: {reason}")
                self.signals.resource_warning.emit(reason)
                self.signals.error.emit((
                    ResourceError,
                    ResourceError(reason),
                    reason
                ))
                return
            
            # Perform work with timeout
            result = self._execute_with_timeout()
            
            # Check if cancelled during work
            if self._is_cancelled:
                logger.info(f"{self.__class__.__name__} cancelled during execution")
                self.signals.cancelled.emit()
                return
            
            # Emit result
            self._result = result
            self.signals.result.emit(result)
            logger.debug(f"{self.__class__.__name__} completed successfully")
            
        except TimeoutError as e:
            # Timeout occurred
            logger.error(f"{self.__class__.__name__} timed out after {self.timeout_seconds}s")
            exc_traceback = traceback.format_exc()
            self.signals.error.emit((
                type(e),
                e,
                f"Operation timed out after {self.timeout_seconds} seconds"
            ))
            
        except Exception as e:
            # Any other error
            logger.error(f"{self.__class__.__name__} failed: {e}")
            exc_traceback = traceback.format_exc()
            self.signals.error.emit((
                type(e),
                e,
                exc_traceback
            ))
            
        finally:
            # Always cleanup and signal finished
            try:
                self.cleanup()
            except Exception as cleanup_error:
                logger.error(f"Cleanup failed: {cleanup_error}")
            
            self.signals.finished.emit()
            logger.debug(f"{self.__class__.__name__} finished (total time: {self.elapsed_time():.2f}s)")
    
    def _execute_with_timeout(self) -> Any:
        """Execute do_work() with timeout enforcement."""
        if self.timeout_seconds <= 0:
            # No timeout
            return self.do_work()
        
        # Execute with timeout check
        result = self.do_work()
        
        # Check if timed out
        if self.elapsed_time() > self.timeout_seconds:
            raise TimeoutError(f"Execution exceeded {self.timeout_seconds} seconds")
        
        return result
    
    def cancel(self):
        """
        Request cancellation of this worker.
        
        The worker will check is_cancelled() and stop gracefully.
        This is cooperative - the worker must check the flag.
        """
        self._is_cancelled = True
        logger.info(f"{self.__class__.__name__} cancellation requested")
    
    def is_cancelled(self) -> bool:
        """
        Check if cancellation has been requested.
        
        Workers should call this periodically in do_work():
            if self.is_cancelled():
                return  # Exit gracefully
        """
        return self._is_cancelled
    
    def report_progress(self, current: int, total: int, message: str = ""):
        """
        Report progress to GUI.
        
        Args:
            current: Current progress value
            total: Total progress value
            message: Optional status message
        """
        if not self._is_cancelled:
            self.signals.progress.emit(current, total, message)
    
    def report_status(self, message: str):
        """
        Report status message to GUI.
        
        Args:
            message: Status message for user
        """
        if not self._is_cancelled:
            self.signals.status.emit(message)
    
    def elapsed_time(self) -> float:
        """
        Get elapsed execution time in seconds.
        
        Returns:
            Seconds since worker started (0 if not started)
        """
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time


class ResourceError(Exception):
    """Raised when insufficient resources to start job."""
    pass

