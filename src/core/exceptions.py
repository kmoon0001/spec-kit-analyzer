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
        details: dict[str, Any] | None = None):
        self.message = message
        self.error_code = error_code or "APPLICATION_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(ApplicationError):
    """Database operation errors."""
