"""
Centralized exception handling for the Therapy Compliance Analyzer.

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

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "DATABASE_ERROR", details)


class SecurityError(ApplicationError):
    """Security-related errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "SECURITY_ERROR", details)


class AIModelError(ApplicationError):
    """AI model operation errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "AI_MODEL_ERROR", details)


class ValidationError(ApplicationError):
    """Input validation errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class ConfigurationError(ApplicationError):
    """Configuration-related errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "CONFIGURATION_ERROR", details)


class DocumentProcessingError(ApplicationError):
    """Document processing and parsing errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "DOCUMENT_PROCESSING_ERROR", details)
