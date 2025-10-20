"""Global exception handler for FastAPI application.

This module provides centralized exception handling for all API endpoints,
ensuring consistent error responses and proper logging without PHI exposure.
"""

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.exceptions import (
    AIModelError,
    ApplicationError,
    ConfigurationError,
    DatabaseError,
    DocumentProcessingError,
    SecurityError,
    ValidationError,
)

logger = structlog.get_logger(__name__)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for all unhandled exceptions.

    Args:
        request: The FastAPI request object
        exc: The exception that was raised

    Returns:
        JSONResponse with appropriate error details

    """
    # Handle custom application errors
    if isinstance(exc, ApplicationError):
        logger.warning(
            "Application error occurred",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=request.url.path,
            method=request.method,
        )
        return JSONResponse(
            status_code=_get_status_code_for_error(exc),
            content={
                "error": exc.error_code,
                "message": _sanitize_error_message(exc.message),
                "details": _sanitize_error_details(exc.details),
            },
        )

    # Handle Starlette HTTP exceptions, which are expected and not server errors
    if isinstance(exc, StarletteHTTPException):
        return await http_exception_handler(request, exc)

    # Handle unexpected server errors
    logger.exception(
        "Unhandled exception: An unexpected error occurred",
        path=request.url.path,
        method=request.method,
        error=str(exc),
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected internal server error occurred. Please contact support.",
            "details": {},
        },
    )


def _get_status_code_for_error(error: ApplicationError) -> int:
    """Map application errors to appropriate HTTP status codes.

    Args:
        error: The application error

    Returns:
        HTTP status code

    """
    error_status_map: dict[type[Exception], int] = {
        DatabaseError: 503,  # Service Unavailable
        SecurityError: 403,  # Forbidden
        AIModelError: 503,  # Service Unavailable
        ValidationError: 422,  # Unprocessable Entity
        ConfigurationError: 500,  # Internal Server Error
        DocumentProcessingError: 422,  # Unprocessable Entity
    }

    # Default to 500 for unmapped ApplicationErrors
    return error_status_map.get(type(error), 500)


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handler for HTTP exceptions with consistent formatting.

    This handler ensures that all HTTP exceptions, whether raised by FastAPI
    or by custom logic, are logged and formatted consistently.

    Args:
        request: The FastAPI request object
        exc: The HTTP exception

    Returns:
        JSONResponse with formatted error details

    """
    logger.info(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP_{exc.status_code}",
            "message": _sanitize_error_message(exc.detail),
            "details": {"path": request.url.path, "method": request.method},
        },
    )


def _sanitize_error_message(message: str) -> str:
    """Sanitize error message to prevent information disclosure."""
    if not message:
        return "An error occurred"

    # Remove sensitive information patterns
    import re

    # Remove file paths
    message = re.sub(r"/[^\s]*", "[PATH]", message)

    # Remove email addresses
    message = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]", message
    )

    # Remove IP addresses
    message = re.sub(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", "[IP]", message)

    # Remove database connection strings
    message = re.sub(
        r"(?:sqlite|postgresql|mysql)://[^\s]*", "[DB_CONNECTION]", message
    )

    # Remove API keys and tokens
    message = re.sub(
        r"(?:api[_-]?key|token|secret|password)[=:]\s*[^\s]+",
        "[CREDENTIAL]",
        message,
        flags=re.IGNORECASE,
    )

    # Remove stack trace information
    message = re.sub(r'File "[^"]*", line \d+', 'File "[PATH]", line [NUMBER]', message)

    # Limit message length
    if len(message) > 500:
        message = message[:500] + "..."

    return message


def _sanitize_error_details(details: dict) -> dict:
    """Sanitize error details to prevent information disclosure."""
    if not details:
        return {}

    sanitized = {}
    sensitive_keys = {
        "password",
        "secret",
        "key",
        "token",
        "credential",
        "auth",
        "file_path",
        "path",
        "url",
        "connection",
        "database",
    }

    for key, value in details.items():
        key_lower = key.lower()

        # Skip sensitive keys
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, str):
            sanitized[key] = _sanitize_error_message(value)
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_error_details(value)
        else:
            sanitized[key] = value

    return sanitized
