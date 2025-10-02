"""
Global exception handler for FastAPI application.

This module provides centralized exception handling for all API endpoints,
ensuring consistent error responses and proper logging without PHI exposure.
"""

import logging

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

logger = logging.getLogger(__name__)


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
        return JSONResponse(
            status_code=_get_status_code_for_error(exc),
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    # Handle Starlette HTTP exceptions
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "HTTP_ERROR", "message": exc.detail, "details": {}},
        )

    # Handle unexpected errors
    logger.error(
        "Unexpected error in %s %s: %s",
        request.method,
        request.url.path,
        str(exc),
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
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
        DatabaseError: 500,
        SecurityError: 403,
        AIModelError: 503,
        ValidationError: 400,
        ConfigurationError: 500,
        DocumentProcessingError: 422,
    }

    return error_status_map.get(type(error), 500)


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handler for HTTP exceptions with consistent formatting.

    Args:
        request: The FastAPI request object
        exc: The HTTP exception

    Returns:
        JSONResponse with formatted error details
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "details": {"path": request.url.path, "method": request.method},
        },
    )
