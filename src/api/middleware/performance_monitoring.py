"""Performance monitoring middleware for FastAPI.

This middleware provides:
- Request/response timing
- Memory usage monitoring
- Database query tracking
- Performance metrics collection
"""

import logging
import time
from typing import Any, Callable, Dict

import psutil
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from ...core.enhanced_logging import get_performance_logger, get_request_logger

logger = logging.getLogger(__name__)


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring API performance."""

    def __init__(self, app: ASGIApp, enable_detailed_logging: bool = True):
        super().__init__(app)
        self.enable_detailed_logging = enable_detailed_logging
        self.performance_logger = get_performance_logger()
        self.request_logger = get_request_logger()

        # Performance metrics
        self.request_count = 0
        self.total_response_time = 0.0
        self.slow_requests = 0  # Requests > 1 second

        logger.info("Performance monitoring middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with performance monitoring."""
        # Start timing
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Extract request info
        method = request.method
        path = request.url.path
        user_id = getattr(request.state, "user_id", None)
        ip_address = request.client.host if request.client else "unknown"

        # Log request
        if self.enable_detailed_logging:
            self.request_logger.log_request(
                method=method, path=path, user_id=user_id, ip_address=ip_address
            )

        # Process request
        try:
            response = await call_next(request)

            # Calculate metrics
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_delta = end_memory - start_memory

            # Update metrics
            self.request_count += 1
            self.total_response_time += duration_ms

            if duration_ms > 1000:  # Slow request threshold
                self.slow_requests += 1

            # Log performance metrics
            self.performance_logger.log_metric(
                "request_duration",
                duration_ms,
                "ms",
                method=method,
                path=path,
                status_code=response.status_code,
                memory_delta_mb=round(memory_delta, 2),
            )

            # Log response
            if self.enable_detailed_logging:
                self.request_logger.log_response(
                    method=method,
                    path=path,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                    user_id=user_id,
                )

            # Add performance headers
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            response.headers["X-Memory-Delta"] = f"{memory_delta:.2f}MB"

            return response

        except Exception as e:
            # Log error with performance context
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {method} {path}",
                extra={
                    "method": method,
                    "path": path,
                    "duration_ms": duration_ms,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        avg_response_time = (
            self.total_response_time / self.request_count
            if self.request_count > 0
            else 0
        )

        return {
            "total_requests": self.request_count,
            "average_response_time_ms": round(avg_response_time, 2),
            "slow_requests": self.slow_requests,
            "slow_request_percentage": round(
                (
                    (self.slow_requests / self.request_count * 100)
                    if self.request_count > 0
                    else 0
                ),
                2,
            ),
            "current_memory_mb": round(
                psutil.Process().memory_info().rss / 1024 / 1024, 2
            ),
            "cpu_percent": psutil.Process().cpu_percent(),
        }


class DatabaseQueryMonitor:
    """Monitor database query performance."""

    def __init__(self):
        self.query_count = 0
        self.total_query_time = 0.0
        self.slow_queries = 0
        self.logger = logging.getLogger("database_performance")

    def log_query(self, query: str, duration_ms: float, **context) -> None:
        """Log a database query."""
        self.query_count += 1
        self.total_query_time += duration_ms

        if duration_ms > 100:  # Slow query threshold
            self.slow_queries += 1
            self.logger.warning(
                f"Slow query detected: {duration_ms:.2f}ms",
                extra={
                    "query": query[:200] + "..." if len(query) > 200 else query,
                    "duration_ms": duration_ms,
                    **context,
                },
            )

        self.logger.debug(
            f"Database query executed",
            extra={
                "query": query[:100] + "..." if len(query) > 100 else query,
                "duration_ms": duration_ms,
                **context,
            },
        )

    def get_query_stats(self) -> Dict[str, Any]:
        """Get database query statistics."""
        avg_query_time = (
            self.total_query_time / self.query_count if self.query_count > 0 else 0
        )

        return {
            "total_queries": self.query_count,
            "average_query_time_ms": round(avg_query_time, 2),
            "slow_queries": self.slow_queries,
            "slow_query_percentage": round(
                (
                    (self.slow_queries / self.query_count * 100)
                    if self.query_count > 0
                    else 0
                ),
                2,
            ),
        }


# Global instances
_performance_middleware: PerformanceMonitoringMiddleware = None
_query_monitor = DatabaseQueryMonitor()


def get_performance_middleware() -> PerformanceMonitoringMiddleware:
    """Get performance monitoring middleware instance."""
    return _performance_middleware


def get_query_monitor() -> DatabaseQueryMonitor:
    """Get database query monitor instance."""
    return _query_monitor


def initialize_performance_monitoring(app: ASGIApp) -> None:
    """Initialize performance monitoring for the application."""
    global _performance_middleware

    _performance_middleware = PerformanceMonitoringMiddleware(app)
    logger.info("Performance monitoring initialized")
