"""Request ID tracking middleware for FastAPI.

This module provides request ID tracking capabilities for better debugging,
security monitoring, and request correlation across services.
"""

import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request IDs to all requests."""

    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID"):
        """
        Initialize request ID middleware.

        Args:
            app: ASGI application
            header_name: HTTP header name for request ID
        """
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and add request ID.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response with request ID header
        """
        # Generate or extract request ID
        request_id = self._get_or_generate_request_id(request)

        # Add request ID to request state
        request.state.request_id = request_id

        # Add request ID to logger context
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            },
        )

        # Process request
        try:
            response = await call_next(request)

            # Add request ID to response headers
            response.headers[self.header_name] = request_id

            # Log successful completion
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                },
            )

            return response

        except Exception as e:
            # Log error with request ID
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    def _get_or_generate_request_id(self, request: Request) -> str:
        """
        Get existing request ID from headers or generate new one.

        Args:
            request: Incoming request

        Returns:
            Request ID string
        """
        # Check if request ID already exists in headers
        existing_id = request.headers.get(self.header_name)
        if existing_id:
            return existing_id

        # Generate new request ID
        return str(uuid.uuid4())


class RequestContext:
    """Context manager for request-specific data."""

    def __init__(self):
        self._context: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        """Set context value."""
        self._context[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get context value."""
        return self._context.get(key, default)

    def clear(self) -> None:
        """Clear all context."""
        self._context.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Get context as dictionary."""
        return self._context.copy()


# Global request context (thread-local in production)
_request_context = RequestContext()


def get_request_context() -> RequestContext:
    """Get current request context."""
    return _request_context


def get_request_id() -> Optional[str]:
    """Get current request ID."""
    return _request_context.get("request_id")


def set_request_id(request_id: str) -> None:
    """Set current request ID."""
    _request_context.set("request_id", request_id)


def log_with_request_id(message: str, level: str = "info", **kwargs) -> None:
    """
    Log message with current request ID.

    Args:
        message: Log message
        level: Log level (info, warning, error, debug)
        **kwargs: Additional log context
    """
    request_id = get_request_id()
    extra = {"request_id": request_id, **kwargs}

    if level == "info":
        logger.info(message, extra=extra)
    elif level == "warning":
        logger.warning(message, extra=extra)
    elif level == "error":
        logger.error(message, extra=extra)
    elif level == "debug":
        logger.debug(message, extra=extra)
    else:
        logger.info(message, extra=extra)


class RequestTracker:
    """Utility class for tracking request metrics and security events."""

    def __init__(self):
        self._metrics: Dict[str, Any] = {}

    def track_request_start(self, request: Request) -> None:
        """Track request start."""
        request_id = get_request_id()
        if not request_id:
            return

        self._metrics[request_id] = {
            "start_time": (
                logger.handlers[0].formatter.formatTime(
                    logger.makeRecord("", 0, "", 0, "", (), None)
                )
                if logger.handlers
                else None
            ),
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "content_length": request.headers.get("content-length"),
        }

    def track_request_end(self, request: Request, response: Response) -> None:
        """Track request completion."""
        request_id = get_request_id()
        if not request_id or request_id not in self._metrics:
            return

        metrics = self._metrics[request_id]
        metrics.update(
            {
                "status_code": response.status_code,
                "response_size": len(response.body) if hasattr(response, "body") else 0,
                "end_time": (
                    logger.handlers[0].formatter.formatTime(
                        logger.makeRecord("", 0, "", 0, "", (), None)
                    )
                    if logger.handlers
                    else None
                ),
            }
        )

        # Log security events
        self._check_security_events(request, response, metrics)

        # Clean up
        del self._metrics[request_id]

    def track_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Track security-related events."""
        request_id = get_request_id()

        log_with_request_id(
            f"Security event: {event_type}",
            level="warning",
            event_type=event_type,
            **details,
        )

    def _check_security_events(
        self, request: Request, response: Response, metrics: Dict[str, Any]
    ) -> None:
        """Check for potential security events."""
        # Check for suspicious patterns
        if response.status_code == 401:
            self.track_security_event(
                "unauthorized_access",
                {
                    "path": request.url.path,
                    "method": request.method,
                    "client_ip": metrics.get("client_ip"),
                },
            )

        elif response.status_code == 403:
            self.track_security_event(
                "forbidden_access",
                {
                    "path": request.url.path,
                    "method": request.method,
                    "client_ip": metrics.get("client_ip"),
                },
            )

        elif response.status_code >= 500:
            self.track_security_event(
                "server_error",
                {
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                },
            )

        # Check for suspicious user agents
        user_agent = metrics.get("user_agent", "")
        if any(
            suspicious in user_agent.lower()
            for suspicious in ["bot", "crawler", "scanner", "sqlmap"]
        ):
            self.track_security_event(
                "suspicious_user_agent",
                {
                    "user_agent": user_agent,
                    "path": request.url.path,
                },
            )


# Global request tracker
_request_tracker = RequestTracker()


def get_request_tracker() -> RequestTracker:
    """Get global request tracker."""
    return _request_tracker
