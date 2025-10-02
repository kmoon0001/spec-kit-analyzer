"""
Error handling decorators and utilities for service-level error management.

This module provides decorators and utilities for consistent error handling
across different service layers.
"""

import logging
from functools import wraps
from typing import Any, Callable, TypeVar, cast

from sqlalchemy.exc import SQLAlchemyError
from .exceptions import DatabaseError, AIModelError, SecurityError

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class ServiceErrorHandler:
    """Service-level error handling decorators."""

    @staticmethod
    def handle_database_error(func: F) -> F:
        """Decorator to handle database-related errors."""

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except SQLAlchemyError as e:
                logger.error("Database error in %s: %s", func.__name__, str(e))
                raise DatabaseError(
                    f"Database operation failed in {func.__name__}",
                    details={"original_error": str(e)},
                )
            except Exception as e:
                logger.error("Unexpected error in %s: %s", func.__name__, str(e))
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SQLAlchemyError as e:
                logger.error("Database error in %s: %s", func.__name__, str(e))
                raise DatabaseError(
                    f"Database operation failed in {func.__name__}",
                    details={"original_error": str(e)},
                )
            except Exception as e:
                logger.error("Unexpected error in %s: %s", func.__name__, str(e))
                raise

        # Return appropriate wrapper based on whether function is async
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    @staticmethod
    def handle_ai_model_error(func: F) -> F:
        """Decorator to handle AI model-related errors."""

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error("AI model error in %s: %s", func.__name__, str(e))
                raise AIModelError(
                    f"AI model operation failed in {func.__name__}",
                    details={"original_error": str(e)},
                )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error("AI model error in %s: %s", func.__name__, str(e))
                raise AIModelError(
                    f"AI model operation failed in {func.__name__}",
                    details={"original_error": str(e)},
                )

        # Return appropriate wrapper based on whether function is async
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    @staticmethod
    def handle_security_error(func: F) -> F:
        """Decorator to handle security-related errors."""

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error("Security error in %s: %s", func.__name__, str(e))
                raise SecurityError(
                    f"Security operation failed in {func.__name__}",
                    details={"original_error": str(e)},
                )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error("Security error in %s: %s", func.__name__, str(e))
                raise SecurityError(
                    f"Security operation failed in {func.__name__}",
                    details={"original_error": str(e)},
                )

        # Return appropriate wrapper based on whether function is async
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)


def log_and_suppress_error(
    error_message: str, return_value: Any = None, log_level: int = logging.ERROR
) -> Callable:
    """
    Decorator to log errors and return a default value instead of raising.
    Useful for non-critical operations where graceful degradation is preferred.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.log(
                    log_level, "%s in %s: %s", error_message, func.__name__, str(e)
                )
                return return_value

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.log(
                    log_level, "%s in %s: %s", error_message, func.__name__, str(e)
                )
                return return_value

        # Return appropriate wrapper based on whether function is async
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    return decorator
