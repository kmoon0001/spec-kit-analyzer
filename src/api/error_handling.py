"""Consolidated error handling system.

This module provides a unified error handling system with proper error codes,
logging, and user-friendly error messages.
"""

import logging
import traceback
from enum import Enum
from typing import Any, Dict, Optional, Union

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Standardized error codes for the application."""

    # Authentication & Authorization
    AUTH_INVALID_CREDENTIALS = "AUTH_001"
    AUTH_TOKEN_EXPIRED = "AUTH_002"
    AUTH_TOKEN_INVALID = "AUTH_003"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_004"
    AUTH_SESSION_EXPIRED = "AUTH_005"
    AUTH_SESSION_INVALID = "AUTH_006"

    # Validation Errors
    VALIDATION_INVALID_INPUT = "VAL_001"
    VALIDATION_MISSING_REQUIRED_FIELD = "VAL_002"
    VALIDATION_INVALID_FORMAT = "VAL_003"
    VALIDATION_FILE_TOO_LARGE = "VAL_004"
    VALIDATION_INVALID_FILE_TYPE = "VAL_005"

    # Business Logic Errors
    BUSINESS_RESOURCE_NOT_FOUND = "BUS_001"
    BUSINESS_RESOURCE_ALREADY_EXISTS = "BUS_002"
    BUSINESS_OPERATION_NOT_ALLOWED = "BUS_003"
    BUSINESS_QUOTA_EXCEEDED = "BUS_004"
    BUSINESS_INVALID_STATE = "BUS_005"

    # System Errors
    SYSTEM_INTERNAL_ERROR = "SYS_001"
    SYSTEM_SERVICE_UNAVAILABLE = "SYS_002"
    SYSTEM_DATABASE_ERROR = "SYS_003"
    SYSTEM_EXTERNAL_SERVICE_ERROR = "SYS_004"
    SYSTEM_TIMEOUT = "SYS_005"

    # Security Errors
    SECURITY_SUSPICIOUS_ACTIVITY = "SEC_001"
    SECURITY_RATE_LIMIT_EXCEEDED = "SEC_002"
    SECURITY_INVALID_REQUEST = "SEC_003"
    SECURITY_BLOCKED_IP = "SEC_004"

    # Analysis Errors
    ANALYSIS_SERVICE_UNAVAILABLE = "ANA_001"
    ANALYSIS_INVALID_DOCUMENT = "ANA_002"
    ANALYSIS_PROCESSING_FAILED = "ANA_003"
    ANALYSIS_TIMEOUT = "ANA_004"
    ANALYSIS_QUOTA_EXCEEDED = "ANA_005"


class ErrorResponse(BaseModel):
    """Standardized error response model."""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    timestamp: str


class AppException(Exception):
    """Base exception class for application-specific errors."""

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        self.error_code = error_code
        self.message = message
        self.details = details
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(AppException):
    """Authentication-related errors."""

    def __init__(self, error_code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(error_code, message, details, status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(AppException):
    """Authorization-related errors."""

    def __init__(self, error_code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(error_code, message, details, status.HTTP_403_FORBIDDEN)


class ValidationError(AppException):
    """Validation-related errors."""

    def __init__(self, error_code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(error_code, message, details, status.HTTP_400_BAD_REQUEST)


class BusinessLogicError(AppException):
    """Business logic-related errors."""

    def __init__(self, error_code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(error_code, message, details, status.HTTP_422_UNPROCESSABLE_ENTITY)


class SystemError(AppException):
    """System-related errors."""

    def __init__(self, error_code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(error_code, message, details, status.HTTP_500_INTERNAL_SERVER_ERROR)


class SecurityError(AppException):
    """Security-related errors."""

    def __init__(self, error_code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(error_code, message, details, status.HTTP_429_TOO_MANY_REQUESTS)


class ErrorHandler:
    """Centralized error handling service."""

    def __init__(self):
        self.error_mappings = {
            # Authentication errors
            "Incorrect username or password": ErrorCode.AUTH_INVALID_CREDENTIALS,
            "Token expired": ErrorCode.AUTH_TOKEN_EXPIRED,
            "Invalid token": ErrorCode.AUTH_TOKEN_INVALID,
            "Not authorized": ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            "Session expired": ErrorCode.AUTH_SESSION_EXPIRED,

            # Validation errors
            "Invalid input": ErrorCode.VALIDATION_INVALID_INPUT,
            "Missing required field": ErrorCode.VALIDATION_MISSING_REQUIRED_FIELD,
            "Invalid format": ErrorCode.VALIDATION_INVALID_FORMAT,
            "File too large": ErrorCode.VALIDATION_FILE_TOO_LARGE,
            "Invalid file type": ErrorCode.VALIDATION_INVALID_FILE_TYPE,

            # Business logic errors
            "Not found": ErrorCode.BUSINESS_RESOURCE_NOT_FOUND,
            "Already exists": ErrorCode.BUSINESS_RESOURCE_ALREADY_EXISTS,
            "Operation not allowed": ErrorCode.BUSINESS_OPERATION_NOT_ALLOWED,
            "Quota exceeded": ErrorCode.BUSINESS_QUOTA_EXCEEDED,

            # System errors
            "Internal server error": ErrorCode.SYSTEM_INTERNAL_ERROR,
            "Service unavailable": ErrorCode.SYSTEM_SERVICE_UNAVAILABLE,
            "Database error": ErrorCode.SYSTEM_DATABASE_ERROR,
            "External service error": ErrorCode.SYSTEM_EXTERNAL_SERVICE_ERROR,
            "Timeout": ErrorCode.SYSTEM_TIMEOUT,

            # Security errors
            "Suspicious activity": ErrorCode.SECURITY_SUSPICIOUS_ACTIVITY,
            "Rate limit exceeded": ErrorCode.SECURITY_RATE_LIMIT_EXCEEDED,
            "Invalid request": ErrorCode.SECURITY_INVALID_REQUEST,
            "Blocked IP": ErrorCode.SECURITY_BLOCKED_IP,

            # Analysis errors
            "Analysis service unavailable": ErrorCode.ANALYSIS_SERVICE_UNAVAILABLE,
            "Invalid document": ErrorCode.ANALYSIS_INVALID_DOCUMENT,
            "Analysis processing failed": ErrorCode.ANALYSIS_PROCESSING_FAILED,
            "Analysis timeout": ErrorCode.ANALYSIS_TIMEOUT,
            "Analysis quota exceeded": ErrorCode.ANALYSIS_QUOTA_EXCEEDED,
        }

    def handle_exception(
        self,
        exc: Exception,
        request: Optional[Request] = None,
        request_id: Optional[str] = None,
    ) -> JSONResponse:
        """
        Handle exception and return appropriate JSON response.

        Args:
            exc: Exception to handle
            request: FastAPI request object
            request_id: Request ID for correlation

        Returns:
            JSONResponse with error details
        """
        # Extract request ID if not provided
        if not request_id and request:
            request_id = getattr(request.state, 'request_id', None)

        # Handle application-specific exceptions
        if isinstance(exc, AppException):
            return self._handle_app_exception(exc, request_id)

        # Handle HTTP exceptions
        if isinstance(exc, HTTPException):
            return self._handle_http_exception(exc, request_id)

        # Handle other exceptions
        return self._handle_generic_exception(exc, request_id)

    def _handle_app_exception(self, exc: AppException, request_id: Optional[str]) -> JSONResponse:
        """Handle application-specific exceptions."""
        error_response = ErrorResponse(
            error_code=exc.error_code.value,
            message=exc.message,
            details=exc.details,
            request_id=request_id,
            timestamp=self._get_timestamp(),
        )

        # Log the error
        logger.error(
            f"Application error: {exc.error_code.value} - {exc.message}",
            extra={
                'error_code': exc.error_code.value,
                'message': exc.message,
                'details': exc.details,
                'request_id': request_id,
            }
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict(),
        )

    def _handle_http_exception(self, exc: HTTPException, request_id: Optional[str]) -> JSONResponse:
        """Handle HTTP exceptions."""
        # Map common HTTP exception messages to error codes
        error_code = self._map_message_to_error_code(exc.detail)

        error_response = ErrorResponse(
            error_code=error_code.value,
            message=exc.detail,
            request_id=request_id,
            timestamp=self._get_timestamp(),
        )

        # Log the error
        logger.warning(
            f"HTTP error: {exc.status_code} - {exc.detail}",
            extra={
                'status_code': exc.status_code,
                'detail': exc.detail,
                'request_id': request_id,
            }
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict(),
        )

    def _handle_generic_exception(self, exc: Exception, request_id: Optional[str]) -> JSONResponse:
        """Handle generic exceptions."""
        error_response = ErrorResponse(
            error_code=ErrorCode.SYSTEM_INTERNAL_ERROR.value,
            message="An unexpected error occurred",
            details={"exception_type": type(exc).__name__},
            request_id=request_id,
            timestamp=self._get_timestamp(),
        )

        # Log the error with full traceback
        logger.error(
            f"Unexpected error: {type(exc).__name__} - {str(exc)}",
            extra={
                'exception_type': type(exc).__name__,
                'exception_message': str(exc),
                'request_id': request_id,
            },
            exc_info=True
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.dict(),
        )

    def _map_message_to_error_code(self, message: str) -> ErrorCode:
        """Map error message to error code."""
        message_lower = message.lower()

        for pattern, error_code in self.error_mappings.items():
            if pattern.lower() in message_lower:
                return error_code

        # Default to internal error for unmapped messages
        return ErrorCode.SYSTEM_INTERNAL_ERROR

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()


# Global error handler instance
_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance."""
    return _error_handler


def handle_exception(exc: Exception, request: Optional[Request] = None) -> JSONResponse:
    """Handle exception using global error handler."""
    return _error_handler.handle_exception(exc, request)


# Convenience functions for common errors
def raise_authentication_error(message: str, details: Optional[Dict[str, Any]] = None):
    """Raise authentication error."""
    raise AuthenticationError(ErrorCode.AUTH_INVALID_CREDENTIALS, message, details)


def raise_authorization_error(message: str, details: Optional[Dict[str, Any]] = None):
    """Raise authorization error."""
    raise AuthorizationError(ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS, message, details)


def raise_validation_error(message: str, details: Optional[Dict[str, Any]] = None):
    """Raise validation error."""
    raise ValidationError(ErrorCode.VALIDATION_INVALID_INPUT, message, details)


def raise_business_logic_error(message: str, details: Optional[Dict[str, Any]] = None):
    """Raise business logic error."""
    raise BusinessLogicError(ErrorCode.BUSINESS_RESOURCE_NOT_FOUND, message, details)


def raise_system_error(message: str, details: Optional[Dict[str, Any]] = None):
    """Raise system error."""
    raise SystemError(ErrorCode.SYSTEM_INTERNAL_ERROR, message, details)


def raise_security_error(message: str, details: Optional[Dict[str, Any]] = None):
    """Raise security error."""
    raise SecurityError(ErrorCode.SECURITY_SUSPICIOUS_ACTIVITY, message, details)