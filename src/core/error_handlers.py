"""Error handling decorators and utilities for the Therapy Compliance Analyzer.

This module provides comprehensive error handling decorators that can be applied
to functions and methods throughout the application to ensure graceful error
handling and appropriate logging.
"""

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from src.core.exceptions import AnalysisError, SecurityError

F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


def handle_analysis_error(func: F) -> F:
    """Decorator to handle analysis-related errors."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception("Analysis error in %s: %s", func.__name__, e)
            raise AnalysisError(
                f"Analysis operation failed in {func.__name__}",
                details={"original_error": str(e)},
            ) from e

    return cast(F, wrapper)


def handle_ai_model_error(func: F) -> F:
    """Decorator to handle AI model-related errors."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception("AI model error in %s: %s", func.__name__, e)
            raise AnalysisError(
                f"AI model operation failed in {func.__name__}",
                details={"original_error": str(e)},
            ) from e

    return cast(F, wrapper)


def handle_security_error(func: F) -> F:
    """Decorator to handle security-related errors."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception("Security error in %s: %s", func.__name__, e)
            raise SecurityError(
                f"Security operation failed in {func.__name__}",
                details={"original_error": str(e)},
            ) from e

    return cast(F, wrapper)


def log_and_suppress_error(error_message: str, return_value: Any = None, log_level: int = logging.ERROR) -> Callable[[F], F]:
    """Decorator to log errors and return a default value instead of raising.

    Useful for non-critical operations where graceful degradation is preferred.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.log(log_level, "%s in %s: %s", error_message, func.__name__, str(e))
                return return_value

        return cast(F, wrapper)

    return decorator
