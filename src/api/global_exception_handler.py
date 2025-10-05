"""
Global exception handler for FastAPI application.

This module provides centralized exception handling for all API endpoints,
ensuring consistent error responses and proper logging without PHI exposure.
"""

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.exceptions import (
    ApplicationError,
    DatabaseError,
    SecurityError,
    AIModelError,
    ValidationError,
    ConfigurationError,
    DocumentProcessingError,
)

logger = structlog.get_logger(__name__)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for all unhandled exceptions.

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
                "message": exc.message,
                "details": exc.details,
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
    """
    Map application errors to appropriate HTTP status codes.

    Args:
        error: The application error

    Returns:
        HTTP status code
    """
    error_status_map = {
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
    """
    Handler for HTTP exceptions with consistent formatting.

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
            "message": exc.detail,
            "details": {"path": request.url.path, "method": request.method},
        },
    )
