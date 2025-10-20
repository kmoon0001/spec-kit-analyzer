"""Advanced request/response logging middleware.

Provides comprehensive logging of API requests and responses including:
- Request/response timing
- Status codes and error tracking
- Request size monitoring
- Performance metrics
- Security event logging
"""

import json
import logging
import time
from typing import Any, Dict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Comprehensive request/response logging middleware."""

    def __init__(self, app, log_body: bool = False, max_body_size: int = 1024):
        super().__init__(app)
        self.log_body = log_body
        self.max_body_size = max_body_size
        self.sensitive_headers = {
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
        }

    async def dispatch(self, request: Request, call_next):
        """Log request and response details."""
        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")

        # Log request details
        await self._log_request(request, request_id)

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log response details
        await self._log_response(request, response, process_time, request_id)

        return response

    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request details."""
        # Sanitize headers
        headers = self._sanitize_headers(dict(request.headers))

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Log basic request info
        logger.info(
            f"Request started | "
            f"id={request_id} | "
            f"method={request.method} | "
            f"url={request.url.path} | "
            f"client_ip={client_ip} | "
            f"user_agent={headers.get('user-agent', 'unknown')[:100]}"
        )

        # Log request body if enabled and not too large
        if self.log_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body and len(body) <= self.max_body_size:
                    try:
                        body_json = json.loads(body.decode())
                        logger.debug(
                            f"Request body | id={request_id} | body={body_json}"
                        )
                    except json.JSONDecodeError:
                        logger.debug(
                            f"Request body (raw) | id={request_id} | body={body.decode()[:200]}"
                        )
            except Exception as e:
                logger.debug(
                    f"Could not read request body | id={request_id} | error={e}"
                )

    async def _log_response(
        self, request: Request, response: Response, process_time: float, request_id: str
    ):
        """Log response details."""
        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = "error"
        elif response.status_code >= 400:
            log_level = "warning"
        else:
            log_level = "info"

        # Get response size
        response_size = response.headers.get("content-length", "unknown")

        # Log response details
        getattr(logger, log_level)(
            f"Request completed | "
            f"id={request_id} | "
            f"method={request.method} | "
            f"url={request.url.path} | "
            f"status={response.status_code} | "
            f"time={process_time:.3f}s | "
            f"size={response_size}"
        )

        # Log slow requests
        if process_time > 5.0:  # Requests taking more than 5 seconds
            logger.warning(
                f"Slow request detected | "
                f"id={request_id} | "
                f"url={request.url.path} | "
                f"time={process_time:.3f}s"
            )

        # Log error responses with more detail
        if response.status_code >= 400:
            logger.error(
                f"Error response | "
                f"id={request_id} | "
                f"status={response.status_code} | "
                f"url={request.url.path} | "
                f"query={str(request.query_params)}"
            )

    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Remove sensitive information from headers."""
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized
