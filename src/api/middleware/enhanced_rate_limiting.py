"""Enhanced rate limiting with per-endpoint configuration.

This module provides comprehensive rate limiting including:
- Per-endpoint rate limits
- User-based rate limiting
- IP-based rate limiting
- Burst protection
- Rate limit headers
"""

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


@dataclass
class RateLimit:
    """Rate limit configuration for an endpoint."""

    requests_per_minute: int
    requests_per_hour: int
    burst_limit: int = 10
    burst_window_seconds: int = 60


class EnhancedRateLimiter:
    """Enhanced rate limiter with per-endpoint configuration."""

    def __init__(self):
        # Default rate limits
        self.default_limits = RateLimit(
            requests_per_minute=60,
            requests_per_hour=1000,
            burst_limit=20,
            burst_window_seconds=60,
        )

        # Per-endpoint rate limits
        self.endpoint_limits: Dict[str, RateLimit] = {
            # Authentication endpoints - stricter limits
            "/auth/token": RateLimit(
                requests_per_minute=10, requests_per_hour=100, burst_limit=5
            ),
            "/auth/register": RateLimit(
                requests_per_minute=5, requests_per_hour=20, burst_limit=3
            ),
            "/auth/users/change-password": RateLimit(
                requests_per_minute=3, requests_per_hour=10, burst_limit=2
            ),
            # Analysis endpoints - moderate limits
            "/analysis/analyze": RateLimit(
                requests_per_minute=20, requests_per_hour=200, burst_limit=10
            ),
            "/analysis/upload": RateLimit(
                requests_per_minute=15, requests_per_hour=150, burst_limit=8
            ),
            # Admin endpoints - strict limits
            "/admin/settings": RateLimit(
                requests_per_minute=5, requests_per_hour=50, burst_limit=3
            ),
            "/admin/users": RateLimit(
                requests_per_minute=10, requests_per_hour=100, burst_limit=5
            ),
            # File operations - moderate limits
            "/analysis/export-pdf": RateLimit(
                requests_per_minute=10, requests_per_hour=100, burst_limit=5
            ),
            # Health and metrics - lenient limits
            "/health": RateLimit(
                requests_per_minute=120, requests_per_hour=2000, burst_limit=50
            ),
            "/metrics": RateLimit(
                requests_per_minute=60, requests_per_hour=1000, burst_limit=30
            ),
        }

        # Request tracking: identifier -> deque of timestamps
        self._request_history: Dict[str, deque] = defaultdict(lambda: deque())

        # Burst tracking: identifier -> deque of timestamps
        self._burst_history: Dict[str, deque] = defaultdict(lambda: deque())

    def is_rate_limited(
        self, request: Request
    ) -> Tuple[bool, Optional[str], Dict[str, int]]:
        """
        Check if request should be rate limited.

        Returns:
            Tuple of (is_limited, reason, headers_dict)
        """
        try:
            # Get client identifier (IP + User ID if authenticated)
            client_id = self._get_client_identifier(request)

            # Get endpoint path
            endpoint_path = self._get_endpoint_path(request)

            # Get rate limit configuration
            rate_limit = self.endpoint_limits.get(endpoint_path, self.default_limits)

            now = time.time()

            # Check burst limit
            burst_limited, burst_reason = self._check_burst_limit(
                client_id, rate_limit, now
            )
            if burst_limited:
                return (
                    True,
                    burst_reason,
                    self._get_rate_limit_headers(rate_limit, 0, 0),
                )

            # Check minute limit
            minute_limited, minute_reason = self._check_minute_limit(
                client_id, rate_limit, now
            )
            if minute_limited:
                return (
                    True,
                    minute_reason,
                    self._get_rate_limit_headers(rate_limit, 0, 0),
                )

            # Check hour limit
            hour_limited, hour_reason = self._check_hour_limit(
                client_id, rate_limit, now
            )
            if hour_limited:
                return True, hour_reason, self._get_rate_limit_headers(rate_limit, 0, 0)

            # Record request
            self._record_request(client_id, now)

            # Calculate remaining requests
            remaining_minute = self._calculate_remaining_minute(
                client_id, rate_limit, now
            )
            remaining_hour = self._calculate_remaining_hour(client_id, rate_limit, now)

            return (
                False,
                None,
                self._get_rate_limit_headers(
                    rate_limit, remaining_minute, remaining_hour
                ),
            )

        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open - don't block requests due to rate limiter errors
            return False, None, {}

    def _get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier."""
        # Get IP address
        ip_address = request.client.host if request.client else "unknown"

        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)

        if user_id:
            return f"user:{user_id}"
        else:
            return f"ip:{ip_address}"

    def _get_endpoint_path(self, request: Request) -> str:
        """Get endpoint path for rate limiting."""
        # Use the route path if available
        if hasattr(request, "route") and request.route:
            return request.route.path

        # Fallback to URL path
        return request.url.path

    def _check_burst_limit(
        self, client_id: str, rate_limit: RateLimit, now: float
    ) -> Tuple[bool, Optional[str]]:
        """Check burst rate limit."""
        burst_window_start = now - rate_limit.burst_window_seconds

        # Clean old burst history
        burst_history = self._burst_history[client_id]
        while burst_history and burst_history[0] < burst_window_start:
            burst_history.popleft()

        # Check if burst limit exceeded
        if len(burst_history) >= rate_limit.burst_limit:
            return (
                True,
                f"Burst limit exceeded: {rate_limit.burst_limit} requests per {rate_limit.burst_window_seconds} seconds",
            )

        # Record burst request
        burst_history.append(now)
        return False, None

    def _check_minute_limit(
        self, client_id: str, rate_limit: RateLimit, now: float
    ) -> Tuple[bool, Optional[str]]:
        """Check requests per minute limit."""
        minute_start = now - 60

        # Clean old history
        request_history = self._request_history[client_id]
        while request_history and request_history[0] < minute_start:
            request_history.popleft()

        # Check if limit exceeded
        if len(request_history) >= rate_limit.requests_per_minute:
            return (
                True,
                f"Rate limit exceeded: {rate_limit.requests_per_minute} requests per minute",
            )

        return False, None

    def _check_hour_limit(
        self, client_id: str, rate_limit: RateLimit, now: float
    ) -> Tuple[bool, Optional[str]]:
        """Check requests per hour limit."""
        hour_start = now - 3600

        # Count requests in the last hour
        request_history = self._request_history[client_id]
        hour_requests = sum(
            1 for timestamp in request_history if timestamp >= hour_start
        )

        # Check if limit exceeded
        if hour_requests >= rate_limit.requests_per_hour:
            return (
                True,
                f"Rate limit exceeded: {rate_limit.requests_per_hour} requests per hour",
            )

        return False, None

    def _record_request(self, client_id: str, now: float):
        """Record a request."""
        self._request_history[client_id].append(now)

    def _calculate_remaining_minute(
        self, client_id: str, rate_limit: RateLimit, now: float
    ) -> int:
        """Calculate remaining requests in current minute."""
        minute_start = now - 60
        request_history = self._request_history[client_id]
        minute_requests = sum(
            1 for timestamp in request_history if timestamp >= minute_start
        )
        return max(0, rate_limit.requests_per_minute - minute_requests)

    def _calculate_remaining_hour(
        self, client_id: str, rate_limit: RateLimit, now: float
    ) -> int:
        """Calculate remaining requests in current hour."""
        hour_start = now - 3600
        request_history = self._request_history[client_id]
        hour_requests = sum(
            1 for timestamp in request_history if timestamp >= hour_start
        )
        return max(0, rate_limit.requests_per_hour - hour_requests)

    def _get_rate_limit_headers(
        self, rate_limit: RateLimit, remaining_minute: int, remaining_hour: int
    ) -> Dict[str, int]:
        """Get rate limit headers."""
        return {
            "X-RateLimit-Limit-Minute": rate_limit.requests_per_minute,
            "X-RateLimit-Remaining-Minute": remaining_minute,
            "X-RateLimit-Limit-Hour": rate_limit.requests_per_hour,
            "X-RateLimit-Remaining-Hour": remaining_hour,
            "X-RateLimit-Burst-Limit": rate_limit.burst_limit,
            "X-RateLimit-Burst-Window": rate_limit.burst_window_seconds,
        }


class EnhancedRateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting middleware."""

    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = EnhancedRateLimiter()

    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiting."""
        try:
            # Skip rate limiting for certain paths
            if self._should_skip_rate_limit(request):
                return await call_next(request)

            # Check rate limit
            is_limited, reason, headers = self.rate_limiter.is_rate_limited(request)

            if is_limited:
                logger.warning(
                    f"Rate limit exceeded: {reason}",
                    client_ip=request.client.host if request.client else "unknown",
                    path=request.url.path,
                )

                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": reason,
                        "retry_after": 60,  # Retry after 60 seconds
                    },
                )

                # Add rate limit headers
                for key, value in headers.items():
                    response.headers[key] = str(value)

                return response

            # Process request
            response = await call_next(request)

            # Add rate limit headers to successful responses
            for key, value in headers.items():
                response.headers[key] = str(value)

            return response

        except Exception as e:
            logger.error(f"Rate limiting middleware error: {e}")
            # Fail open - don't block requests due to middleware errors
            return await call_next(request)

    def _should_skip_rate_limit(self, request: Request) -> bool:
        """Determine if rate limiting should be skipped."""
        # Skip for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return True

        # Skip for health checks
        if request.url.path in ["/health", "/metrics"]:
            return True

        return False


# Global rate limiter instance
_rate_limiter: Optional[EnhancedRateLimiter] = None


def get_rate_limiter() -> EnhancedRateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = EnhancedRateLimiter()
    return _rate_limiter
