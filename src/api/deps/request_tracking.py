"""Request tracking dependencies for FastAPI endpoints.

This module provides dependencies for accessing request tracking information
in FastAPI endpoints.
"""

from typing import Optional

from fastapi import Depends, Request
from starlette.types import ASGIApp

from src.api.middleware.request_tracking import get_request_id, log_with_request_id


def get_request_id_dependency(request: Request) -> Optional[str]:
    """
    Dependency to get current request ID.

    Args:
        request: FastAPI request object

    Returns:
        Request ID if available
    """
    return getattr(request.state, 'request_id', None)


def log_with_request_context(message: str, level: str = "info", **kwargs):
    """
    Dependency factory for logging with request context.

    Args:
        message: Log message
        level: Log level
        **kwargs: Additional context

    Returns:
        Function that logs with request context
    """
    def _log():
        log_with_request_id(message, level, **kwargs)

    return _log


# Common dependencies
RequestId = Depends(get_request_id_dependency)
