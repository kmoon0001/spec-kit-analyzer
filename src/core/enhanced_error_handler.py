"""Enhanced Error Handling System
import numpy as np

Provides comprehensive error handling, recovery mechanisms, and user-friendly
error reporting for all system components.
"""

import logging
import traceback
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ErrorCategory(Enum):
    """Error categories for better classification."""

    SYSTEM = "system"
    USER_INPUT = "user_input"
    NETWORK = "network"
    AI_MODEL = "ai_model"
    DATA_PROCESSING = "data_processing"
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    CONFIGURATION = "configuration"


@dataclass
class ErrorContext:
    """Context information for error handling."""

    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    component: str
    user_id: int | None = None
    operation: str | None = None
    additional_data: dict[str, Any] = None


class EnhancedError(Exception):
    """Enhanced exception class with rich context and recovery suggestions."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        component: str = "unknown",
        user_message: str | None = None,
        recovery_suggestions: list[str] | None = None,
        technical_details: dict[str, Any] | None = None,
        original_exception: Exception | None = None,
    ):
        super().__init__(message)

        self.error_id = str(uuid.uuid4())
        self.timestamp = datetime.now()
        self.severity = severity
        self.category = category
        self.component = component
        self.user_message = user_message or self._generate_user_friendly_message()
        self.recovery_suggestions = recovery_suggestions or []
        self.technical_details = technical_details or {}
        self.original_exception = original_exception

    def _generate_user_friendly_message(self) -> str:
        """Generate user-friendly error message based on category."""
        messages = {
            ErrorCategory.SYSTEM: "A system error occurred. Our team has been notified and is working on a fix.",
            ErrorCategory.USER_INPUT: "There was an issue with the provided information. Please check your input and try again.",
            ErrorCategory.NETWORK: "Unable to connect to the service. Please check your internet connection and try again.",
            ErrorCategory.AI_MODEL: "The AI analysis service is temporarily unavailable. Please try again in a few moments.",
            ErrorCategory.DATA_PROCESSING: "There was an issue processing your document. Please verify the file format and try again.",
            ErrorCategory.AUTHENTICATION: "Authentication failed. Please check your credentials and try again.",
            ErrorCategory.PERMISSION: "You don't have permission to perform this action. Please contact your administrator.",
            ErrorCategory.CONFIGURATION: "There's a configuration issue. Please contact your system administrator.",
        }
        return messages.get(self.category, "An unexpected error occurred. Please try again or contact support.")

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for API responses."""
        return {
            "error_id": self.error_id,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "category": self.category.value,
            "component": self.component,
            "message": str(self),
            "user_message": self.user_message,
            "recovery_suggestions": self.recovery_suggestions,
            "technical_details": self.technical_details,
        }


class ErrorHandler:
    """Comprehensive error handling system with recovery mechanisms.

    This system provides:
    - Intelligent error classification and severity assessment
    - User-friendly error messages with recovery suggestions
    - Automatic retry mechanisms for transient errors
    - Error pattern detection and prevention
    - Comprehensive logging and monitoring

    Example:
        >>> error_handler = ErrorHandler()
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     handled_error = error_handler.handle_error(e, component="pdf_export")
        ...     return handled_error.to_dict()

    """

    def __init__(self):
        """Initialize the error handler."""
        self.error_history = []
        self.max_history_size = 1000

    def handle_error(
        self,
        exception: Exception,
        component: str,
        operation: str | None = None,
        user_id: int | None = None,
        context: dict[str, Any] | None = None,
    ) -> EnhancedError:
        """Handle an exception with enhanced error processing.

        Args:
            exception: The original exception
            component: Component where the error occurred
            operation: Operation being performed when error occurred
            user_id: ID of the user (if applicable)
            context: Additional context information

        Returns:
            EnhancedError with comprehensive error information

        """
        try:
            # Classify the error
            severity, category = self._classify_error(exception, component)

            # Generate recovery suggestions
            recovery_suggestions = self._get_recovery_suggestions(exception, category, component)

            # Create enhanced error
            enhanced_error = EnhancedError(
                message=str(exception),
                severity=severity,
                category=category,
                component=component,
                recovery_suggestions=recovery_suggestions,
                technical_details={
                    "exception_type": type(exception).__name__,
                    "traceback": traceback.format_exc(),
                    "context": context or {},
                    "operation": operation,
                },
                original_exception=exception,
            )

            # Log the error
            self._log_error(enhanced_error, user_id)

            # Store in history for pattern analysis
            self._store_error_history(enhanced_error)

            # Check for error patterns
            self._analyze_error_patterns(enhanced_error)

            return enhanced_error

        except Exception as handler_error:
            # Fallback error handling
            logger.critical("Error handler itself failed: %s", handler_error)
            return EnhancedError(
                message="Critical system error occurred",
                severity=ErrorSeverity.CRITICAL,
                category=ErrorCategory.SYSTEM,
                component="error_handler",
            )

    async def handle_with_retry(
        self, operation: Callable, max_retries: int = 3, component: str = "unknown", backoff_factor: float = 1.0
    ) -> Any:
        """Execute an operation with automatic retry on transient errors.

        Args:
            operation: The operation to execute
            max_retries: Maximum number of retry attempts
            component: Component name for error tracking
            backoff_factor: Exponential backoff factor for retries

        Returns:
            Result of the operation

        Raises:
            EnhancedError: If all retry attempts fail

        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    # Exponential backoff
                    import asyncio

                    await asyncio.sleep(backoff_factor * (2 ** (attempt - 1)))

                return await operation() if asyncio.iscoroutinefunction(operation) else operation()

            except (ImportError, ModuleNotFoundError, AttributeError) as e:
                last_exception = e

                # Check if error is retryable
                if not self._is_retryable_error(e):
                    break

                if attempt < max_retries:
                    logger.warning("Operation failed (attempt %s/{max_retries + 1}): {e}", attempt + 1)
                    continue

        # All retries failed
        return self.handle_error(last_exception, component, "retry_operation")

    def _classify_error(self, exception: Exception, component: str) -> tuple[ErrorSeverity, ErrorCategory]:
        """Classify error severity and category."""
        exception_type = type(exception).__name__
        exception_message = str(exception).lower()

        # Category classification
        if (
            "permission" in exception_message
            or "unauthorized" in exception_message
            or "access denied" in exception_message
        ):
            category = ErrorCategory.PERMISSION
        elif "authentication" in exception_message or "login" in exception_message:
            category = ErrorCategory.AUTHENTICATION
        elif "network" in exception_message or "connection" in exception_message:
            category = ErrorCategory.NETWORK
        elif "model" in exception_message or "ai" in exception_message:
            category = ErrorCategory.AI_MODEL
        elif "config" in exception_message or "setting" in exception_message:
            category = ErrorCategory.CONFIGURATION
        elif "input" in exception_message or "validation" in exception_message:
            category = ErrorCategory.USER_INPUT
        elif "processing" in exception_message or "parse" in exception_message:
            category = ErrorCategory.DATA_PROCESSING
        else:
            category = ErrorCategory.SYSTEM

        # Severity classification
        if exception_type in ["SystemExit", "KeyboardInterrupt", "MemoryError"]:
            severity = ErrorSeverity.CRITICAL
        elif exception_type in ["ConnectionError", "TimeoutError", "OSError"]:
            severity = ErrorSeverity.HIGH
        elif exception_type in ["ValueError", "TypeError", "AttributeError"]:
            severity = ErrorSeverity.MEDIUM
        elif exception_type in ["FileNotFoundError", "PermissionError"]:
            severity = ErrorSeverity.LOW
        else:
            severity = ErrorSeverity.MEDIUM

        return severity, category

    def _get_recovery_suggestions(self, exception: Exception, category: ErrorCategory, component: str) -> list[str]:
        """Generate recovery suggestions based on error type."""
        suggestions = []

        # Category-specific suggestions
        category_suggestions = {
            ErrorCategory.NETWORK: [
                "Check your internet connection",
                "Try again in a few moments",
                "Contact your network administrator if the problem persists",
            ],
            ErrorCategory.USER_INPUT: [
                "Verify that all required fields are filled out correctly",
                "Check file format and size requirements",
                "Review the input guidelines and try again",
            ],
            ErrorCategory.AI_MODEL: [
                "The AI service may be temporarily overloaded - try again shortly",
                "Try with a smaller document or simpler request",
                "Contact support if the issue continues",
            ],
            ErrorCategory.DATA_PROCESSING: [
                "Verify the document format is supported",
                "Try with a different document",
                "Check that the file is not corrupted",
            ],
            ErrorCategory.AUTHENTICATION: [
                "Check your username and password",
                "Try logging out and logging back in",
                "Contact your administrator to reset your credentials",
            ],
            ErrorCategory.PERMISSION: [
                "Contact your administrator for the necessary permissions",
                "Verify you're logged in with the correct account",
                "Check if your account has the required access level",
            ],
            ErrorCategory.CONFIGURATION: [
                "Contact your system administrator",
                "Check the application configuration",
                "Restart the application if possible",
            ],
            ErrorCategory.SYSTEM: [
                "Try the operation again",
                "Restart the application if the problem persists",
                "Contact technical support if the issue continues",
            ],
        }

        suggestions.extend(category_suggestions.get(category, []))

        # Component-specific suggestions
        if component == "pdf_export":
            suggestions.extend(
                [
                    "Ensure the PDF export service is properly configured",
                    "Try exporting a smaller report",
                    "Check available disk space",
                ]
            )
        elif component == "plugin_system":
            suggestions.extend(
                [
                    "Verify the plugin is compatible with this version",
                    "Check plugin dependencies",
                    "Try disabling and re-enabling the plugin",
                ]
            )
        elif component == "ehr_integration":
            suggestions.extend(
                [
                    "Verify EHR system credentials and connection settings",
                    "Check if the EHR system is accessible",
                    "Contact your EHR administrator",
                ]
            )

        return suggestions[:5]  # Limit to top 5 suggestions

    def _is_retryable_error(self, exception: Exception) -> bool:
        """Determine if an error is retryable."""
        retryable_types = [
            "ConnectionError",
            "TimeoutError",
            "TemporaryFailure",
            "ServiceUnavailable",
        ]

        retryable_messages = [
            "timeout",
            "connection reset",
            "service unavailable",
            "temporary failure",
        ]

        exception_type = type(exception).__name__
        exception_message = str(exception).lower()

        return exception_type in retryable_types or any(msg in exception_message for msg in retryable_messages)

    def _log_error(self, error: EnhancedError, user_id: int | None):
        """Log error with appropriate level and context."""
        log_data = {
            "error_id": error.error_id,
            "component": error.component,
            "category": error.category.value,
            "user_id": user_id,
        }

        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical("Critical error: %s", error, extra=log_data)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error("High severity error: %s", error, extra=log_data)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning("Medium severity error: %s", error, extra=log_data)
        else:
            logger.info("Low severity error: %s", error, extra=log_data)

    def _store_error_history(self, error: EnhancedError):
        """Store error in history for pattern analysis."""
        self.error_history.append(
            {
                "timestamp": error.timestamp,
                "component": error.component,
                "category": error.category.value,
                "severity": error.severity.value,
                "error_type": type(error.original_exception).__name__ if error.original_exception else "Unknown",
            }
        )

        # Maintain history size limit
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size :]

    def _analyze_error_patterns(self, error: EnhancedError):
        """Analyze error patterns for proactive prevention."""
        # Simple pattern detection - in production, this would be more sophisticated
        recent_errors = [e for e in self.error_history[-10:] if e["component"] == error.component]

        if len(recent_errors) >= 3:
            logger.warning("Error pattern detected in %s: {len(recent_errors)} recent errors", error.component)

    def _initialize_recovery_strategies(self):
        """Initialize recovery strategies for different error types."""
        self.recovery_strategies = {
            "ConnectionError": self._recover_connection_error,
            "TimeoutError": self._recover_timeout_error,
            "MemoryError": self._recover_memory_error,
            "FileNotFoundError": self._recover_file_not_found_error,
        }

    def _recover_connection_error(self, context: dict[str, Any]) -> dict[str, Any]:
        """Recovery strategy for connection errors."""
        return {
            "retry_recommended": True,
            "retry_delay": 5,
            "max_retries": 3,
            "fallback_action": "use_cached_data",
        }

    def _recover_timeout_error(self, context: dict[str, Any]) -> dict[str, Any]:
        """Recovery strategy for timeout errors."""
        return {
            "retry_recommended": True,
            "retry_delay": 10,
            "max_retries": 2,
            "fallback_action": "reduce_request_size",
        }

    def _recover_memory_error(self, context: dict[str, Any]) -> dict[str, Any]:
        """Recovery strategy for memory errors."""
        return {
            "retry_recommended": False,
            "immediate_action": "reduce_processing_load",
            "fallback_action": "process_in_chunks",
        }

    def _recover_file_not_found_error(self, context: dict[str, Any]) -> dict[str, Any]:
        """Recovery strategy for file not found errors."""
        return {
            "retry_recommended": False,
            "immediate_action": "verify_file_path",
            "fallback_action": "use_default_file",
        }


# Global enhanced error handler instance
# Global enhanced error handler instance
# Global enhanced error handler instance
enhanced_error_handler = ErrorHandler()
