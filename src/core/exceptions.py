"""Centralized exception handling for the Therapy Compliance Analyzer.

This module defines custom exception classes and error handling utilities
to provide consistent error management across the application.
"""

from typing import Any


class ApplicationError(Exception):
    """Base exception for application-specific errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code or "APPLICATION_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(ApplicationError):
    """Database operation errors."""


class AIModelError(ApplicationError):
    """AI model operation errors."""

    def __init__(self, message: str, model_name: str | None = None, **kwargs):
        self.model_name = model_name
        super().__init__(message, error_code="AI_MODEL_ERROR", **kwargs)


class ConfigurationError(ApplicationError):
    """Configuration-related errors."""

    pass


class AnalysisError(ApplicationError):
    """Analysis operation errors."""

    pass


class DocumentProcessingError(ApplicationError):
    """Document processing errors."""

    pass


class SecurityError(ApplicationError):
    """Security-related errors."""

    pass


class ValidationError(ApplicationError):
    """Validation errors."""

    pass
