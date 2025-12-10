"""Comprehensive Type Safety and Error Handling for Clinical Compliance Analysis.

This module provides comprehensive type safety, error handling, and validation
using expert patterns and best practices for healthcare applications.

Features:
- Comprehensive type definitions and protocols
- Advanced error handling with context
- Input validation and sanitization
- Result types for safe operations
- Comprehensive logging integration
- Audit trail integration
- Performance monitoring
"""

import asyncio
import functools
import logging
import re
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, Generic, Protocol, runtime_checkable
import uuid
from contextlib import contextmanager, asynccontextmanager
import os

from src.core.centralized_logging import get_logger, audit_logger, performance_tracker

# Type definitions
T = TypeVar('T')
E = TypeVar('E', bound=Exception)
R = TypeVar('R')


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK = "network"
    DATABASE = "database"
    ML_MODEL = "ml_model"
    CACHE = "cache"
    SECURITY = "security"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"


@dataclass
class ErrorContext:
    """Comprehensive error context information."""
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.SYSTEM
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    is_recoverable: bool = True
    suggested_action: Optional[str] = None


@dataclass
class ValidationError(ErrorContext):
    """Validation error with specific context."""
    field_name: Optional[str] = None
    field_value: Optional[Any] = None
    validation_rule: Optional[str] = None
    expected_format: Optional[str] = None


@dataclass
class SecurityError(ErrorContext):
    """Security-related error."""
    threat_type: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    attack_vector: Optional[str] = None


class Result(Generic[T, E]):
    """Result type for safe operations that can fail."""

    def __init__(self, value: Optional[T] = None, error: Optional[E] = None):
        self._value = value
        self._error = error

    @property
    def is_success(self) -> bool:
        """Check if the result is successful."""
        return self._error is None

    @property
    def is_failure(self) -> bool:
        """Check if the result is a failure."""
        return self._error is not None

    @property
    def value(self) -> T:
        """Get the value if successful."""
        if self._error is not None:
            raise ValueError("Cannot get value from failed result")
        return self._value

    @property
    def error(self) -> E:
        """Get the error if failed."""
        if self._error is None:
            raise ValueError("Cannot get error from successful result")
        return self._error

    def map(self, func: Callable[[T], R]) -> 'Result[R, E]':
        """Map the value if successful."""
        if self.is_success:
            try:
                return Result.success(func(self._value))
            except Exception as e:
                return Result.failure(e)
        return Result.failure(self._error)

    def flat_map(self, func: Callable[[T], 'Result[R, E]']) -> 'Result[R, E]':
        """Flat map the value if successful."""
        if self.is_success:
            return func(self._value)
        return Result.failure(self._error)

    def recover(self, func: Callable[[E], T]) -> 'Result[T, E]':
        """Recover from error."""
        if self.is_failure:
            try:
                return Result.success(func(self._error))
            except Exception as e:
                return Result.failure(e)
        return self

    @staticmethod
    def success(value: T) -> 'Result[T, E]':
        """Create a successful result."""
        return Result(value=value, error=None)

    @staticmethod
    def failure(error: E) -> 'Result[T, E]':
        """Create a failed result."""
        return Result(value=None, error=error)


@runtime_checkable
class Validator(Protocol):
    """Protocol for input validators."""

    def validate(self, value: Any) -> Result[Any, ValidationError]:
        """Validate a value."""
        ...


class StringValidator:
    """String validation with comprehensive checks."""

    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        required: bool = True,
        allow_empty: bool = False
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.required = required
        self.allow_empty = allow_empty

    def validate(self, value: Any) -> Result[str, ValidationError]:
        """Validate string value."""
        # Check if value is provided
        if value is None:
            if self.required:
                return Result.failure(ValidationError(
                    message="Value is required",
                    severity=ErrorSeverity.MEDIUM,
                    category=ErrorCategory.VALIDATION,
                    validation_rule="required"
                ))
            return Result.success("")

        # Convert to string
        try:
            str_value = str(value)
        except Exception as e:
            return Result.failure(ValidationError(
                message=f"Cannot convert to string: {e}",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION,
                validation_rule="string_conversion"
            ))

        # Check empty
        if not str_value and not self.allow_empty:
            return Result.failure(ValidationError(
                message="String cannot be empty",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION,
                validation_rule="non_empty"
            ))

        # Check length
        if self.min_length is not None and len(str_value) < self.min_length:
            return Result.failure(ValidationError(
                message=f"String too short (minimum {self.min_length} characters)",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION,
                validation_rule="min_length",
                field_value=str_value
            ))

        if self.max_length is not None and len(str_value) > self.max_length:
            return Result.failure(ValidationError(
                message=f"String too long (maximum {self.max_length} characters)",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION,
                validation_rule="max_length",
                field_value=str_value
            ))

        # Check pattern
        if self.pattern and not re.match(self.pattern, str_value):
            return Result.failure(ValidationError(
                message=f"String does not match required pattern",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION,
                validation_rule="pattern_match",
                field_value=str_value,
                expected_format=self.pattern
            ))

        return Result.success(str_value)


class NumberValidator:
    """Number validation with comprehensive checks."""

    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        integer_only: bool = False,
        required: bool = True
    ):
        self.min_value = min_value
        self.max_value = max_value
        self.integer_only = integer_only
        self.required = required

    def validate(self, value: Any) -> Result[Union[int, float], ValidationError]:
        """Validate number value."""
        # Check if value is provided
        if value is None:
            if self.required:
                return Result.failure(ValidationError(
                    message="Value is required",
                    severity=ErrorSeverity.MEDIUM,
                    category=ErrorCategory.VALIDATION,
                    validation_rule="required"
                ))
            return Result.success(0)

        # Convert to number
        try:
            if self.integer_only:
                num_value = int(value)
            else:
                num_value = float(value)
        except (ValueError, TypeError) as e:
            return Result.failure(ValidationError(
                message=f"Cannot convert to number: {e}",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION,
                validation_rule="number_conversion",
                field_value=value
            ))

        # Check range
        if self.min_value is not None and num_value < self.min_value:
            return Result.failure(ValidationError(
                message=f"Value too small (minimum {self.min_value})",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION,
                validation_rule="min_value",
                field_value=num_value
            ))

        if self.max_value is not None and num_value > self.max_value:
            return Result.failure(ValidationError(
                message=f"Value too large (maximum {self.max_value})",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION,
                validation_rule="max_value",
                field_value=num_value
            ))

        return Result.success(num_value)


class EmailValidator:
    """Email validation with comprehensive checks."""

    def __init__(self, required: bool = True):
        self.required = required
        self.email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    def validate(self, value: Any) -> Result[str, ValidationError]:
        """Validate email value."""
        if value is None:
            if self.required:
                return Result.failure(ValidationError(
                    message="Email is required",
                    severity=ErrorSeverity.MEDIUM,
                    category=ErrorCategory.VALIDATION,
                    validation_rule="required"
                ))
            return Result.success("")

        str_value = str(value).strip()

        if not str_value:
            if self.required:
                return Result.failure(ValidationError(
                    message="Email cannot be empty",
                    severity=ErrorSeverity.MEDIUM,
                    category=ErrorCategory.VALIDATION,
                    validation_rule="non_empty"
                ))
            return Result.success("")

        if not re.match(self.email_pattern, str_value):
            return Result.failure(ValidationError(
                message="Invalid email format",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION,
                validation_rule="email_format",
                field_value=str_value,
                expected_format="user@domain.com"
            ))

        if len(str_value) > 254:  # RFC 5321 limit
            return Result.failure(ValidationError(
                message="Email too long (maximum 254 characters)",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION,
                validation_rule="max_length",
                field_value=str_value
            ))

        return Result.success(str_value)


class ErrorHandler:
    """Comprehensive error handling with context and recovery."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or get_logger(__name__)
        self.error_history: List[ErrorContext] = []
        self.max_history_size = 1000

    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        component: Optional[str] = None,
        operation: Optional[str] = None
    ) -> ErrorContext:
        """Handle error with comprehensive context."""

        error_context = ErrorContext(
            message=str(error),
            severity=severity,
            category=category,
            details=context or {},
            stack_trace=traceback.format_exc(),
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            component=component,
            operation=operation,
            suggested_action=self._get_suggested_action(error, category)
        )

        # Log error
        self._log_error(error_context)

        # Store in history
        self._store_error(error_context)

        # Log audit event
        audit_logger.log_system_event(
            event_type="error",
            description=f"Error in {component or 'unknown'}: {error_context.message}",
            severity=severity.value.upper(),
            details=error_context.details
        )

        return error_context

    def _log_error(self, error_context: ErrorContext) -> None:
        """Log error with appropriate level."""
        log_level = {
            ErrorSeverity.LOW: logging.DEBUG,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error_context.severity, logging.ERROR)

        self.logger.log(
            log_level,
            "Error occurred: %s",
            error_context.message,
            extra={
                'error_context': error_context.__dict__,
                'error_id': error_context.error_id
            }
        )

    def _store_error(self, error_context: ErrorContext) -> None:
        """Store error in history."""
        self.error_history.append(error_context)

        # Keep only recent errors
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]

    def _get_suggested_action(self, error: Exception, category: ErrorCategory) -> str:
        """Get suggested action based on error type."""
        suggestions = {
            ErrorCategory.VALIDATION: "Check input data and validation rules",
            ErrorCategory.AUTHENTICATION: "Verify credentials and authentication status",
            ErrorCategory.AUTHORIZATION: "Check user permissions and roles",
            ErrorCategory.NETWORK: "Check network connectivity and retry",
            ErrorCategory.DATABASE: "Check database connection and retry",
            ErrorCategory.ML_MODEL: "Check model availability and retry",
            ErrorCategory.CACHE: "Clear cache and retry",
            ErrorCategory.SECURITY: "Review security logs and contact administrator",
            ErrorCategory.BUSINESS_LOGIC: "Review business rules and data integrity",
            ErrorCategory.SYSTEM: "Check system resources and contact administrator"
        }

        return suggestions.get(category, "Contact system administrator")

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        if not self.error_history:
            return {"total_errors": 0}

        # Count by severity
        severity_counts = {}
        for error in self.error_history:
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Count by category
        category_counts = {}
        for error in self.error_history:
            category = error.category.value
            category_counts[category] = category_counts.get(category, 0) + 1

        # Recent errors (last 24 hours)
        recent_cutoff = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        recent_errors = [e for e in self.error_history if e.timestamp >= recent_cutoff]

        return {
            "total_errors": len(self.error_history),
            "recent_errors_24h": len(recent_errors),
            "severity_distribution": severity_counts,
            "category_distribution": category_counts,
            "most_common_errors": self._get_most_common_errors()
        }

    def _get_most_common_errors(self) -> List[Dict[str, Any]]:
        """Get most common error messages."""
        error_counts = {}
        for error in self.error_history:
            message = error.message
            error_counts[message] = error_counts.get(message, 0) + 1

        # Sort by count and return top 10
        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"message": msg, "count": count} for msg, count in sorted_errors[:10]]


class SafeExecutor:
    """Safe execution wrapper with comprehensive error handling."""

    def __init__(self, error_handler: Optional[ErrorHandler] = None):
        self.error_handler = error_handler or ErrorHandler()

    def execute(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> Result[T, ErrorContext]:
        """Execute function safely with error handling."""
        try:
            result = func(*args, **kwargs)
            return Result.success(result)
        except Exception as e:
            error_context = self.error_handler.handle_error(
                error=e,
                context={"function": func.__name__, "args": str(args), "kwargs": str(kwargs)},
                component=func.__module__,
                operation=func.__name__
            )
            return Result.failure(error_context)

    async def execute_async(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> Result[T, ErrorContext]:
        """Execute async function safely with error handling."""
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            return Result.success(result)
        except Exception as e:
            error_context = self.error_handler.handle_error(
                error=e,
                context={"function": func.__name__, "args": str(args), "kwargs": str(kwargs)},
                component=func.__module__,
                operation=func.__name__
            )
            return Result.failure(error_context)


def safe_execute(
    error_handler: Optional[ErrorHandler] = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.SYSTEM
):
    """Decorator for safe function execution."""
    def decorator(func: Callable[..., T]) -> Callable[..., Result[T, ErrorContext]]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Result[T, ErrorContext]:
            executor = SafeExecutor(error_handler)
            return executor.execute(func, *args, **kwargs)
        return wrapper
    return decorator


def safe_execute_async(
    error_handler: Optional[ErrorHandler] = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.SYSTEM
):
    """Decorator for safe async function execution."""
    def decorator(func: Callable[..., T]) -> Callable[..., Result[T, ErrorContext]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Result[T, ErrorContext]:
            executor = SafeExecutor(error_handler)
            return await executor.execute_async(func, *args, **kwargs)
        return wrapper
    return decorator


@contextmanager
def error_context(
    operation: str,
    component: Optional[str] = None,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None
):
    """Context manager for error handling."""
    error_handler = ErrorHandler()

    try:
        yield error_handler
    except Exception as e:
        error_context = error_handler.handle_error(
            error=e,
            operation=operation,
            component=component,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id
        )
        raise


@asynccontextmanager
async def async_error_context(
    operation: str,
    component: Optional[str] = None,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None
):
    """Async context manager for error handling."""
    error_handler = ErrorHandler()

    try:
        yield error_handler
    except Exception as e:
        error_context = error_handler.handle_error(
            error=e,
            operation=operation,
            component=component,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id
        )
        raise


class InputSanitizer:
    """Comprehensive input sanitization."""

    @staticmethod
    def sanitize_string(value: Any, max_length: Optional[int] = None) -> str:
        """Sanitize string input."""
        if value is None:
            return ""

        # Convert to string
        str_value = str(value)

        # Remove control characters except newlines and tabs
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', str_value)

        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized)

        # Trim whitespace
        sanitized = sanitized.strip()

        # Limit length if specified
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length-3] + "..."

        return sanitized

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for security."""
        # Remove path traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')

        # Remove control characters
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)

        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext

        return filename

    @staticmethod
    def sanitize_json(data: Any) -> Dict[str, Any]:
        """Sanitize JSON data."""
        if isinstance(data, dict):
            return {k: InputSanitizer.sanitize_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [InputSanitizer.sanitize_json(item) for item in data]
        elif isinstance(data, str):
            return InputSanitizer.sanitize_string(data)
        else:
            return data


# Global instances
error_handler = ErrorHandler()
safe_executor = SafeExecutor(error_handler)
input_sanitizer = InputSanitizer()

# Common validators
email_validator = EmailValidator()
string_validator = StringValidator(min_length=1, max_length=1000)
number_validator = NumberValidator(min_value=0, max_value=1000000)
filename_validator = StringValidator(pattern=r'^[a-zA-Z0-9._-]+$', max_length=255)
