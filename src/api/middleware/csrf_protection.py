"""CSRF Protection Middleware for FastAPI.

This module provides comprehensive CSRF protection using double-submit cookie pattern
and token validation for state-changing operations.
"""

import hashlib
import hmac
import logging
import secrets
from typing import Optional

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware using double-submit cookie pattern."""

    def __init__(self, app, secret_key: str, cookie_name: str = "csrf_token", header_name: str = "X-CSRF-Token"):
        super().__init__(app)
        self.secret_key = secret_key.encode() if isinstance(secret_key, str) else secret_key
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.cookie_max_age = 3600  # 1 hour
        self.cookie_secure = True  # HTTPS only
        self.cookie_httponly = False  # Allow JavaScript access for double-submit
        self.cookie_samesite = "strict"

    async def dispatch(self, request: Request, call_next):
        """Process request through CSRF protection."""
        try:
            # Skip CSRF for safe methods and certain endpoints
            if self._should_skip_csrf(request):
                return await call_next(request)

            # Handle CSRF token generation for GET requests
            if request.method == "GET":
                response = await call_next(request)
                self._set_csrf_cookie(response)
                return response

            # Validate CSRF token for state-changing methods
            if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
                if not self._validate_csrf_token(request):
                    logger.warning(f"CSRF validation failed for {request.method} {request.url}")
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "error": "CSRF_TOKEN_INVALID",
                            "message": "CSRF token validation failed. Please refresh the page and try again."
                        }
                    )

            response = await call_next(request)

            # Set CSRF cookie for successful requests
            if response.status_code < 400:
                self._set_csrf_cookie(response)

            return response

        except Exception as e:
            logger.error(f"CSRF middleware error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "CSRF_MIDDLEWARE_ERROR", "message": "Internal server error"}
            )

    def _should_skip_csrf(self, request: Request) -> bool:
        """Determine if CSRF protection should be skipped for this request."""
        # Skip for safe methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        # Skip for certain API endpoints that don't need CSRF
        skip_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/auth/token",  # OAuth2 token endpoint
            "/auth/register",  # Registration endpoint
        ]

        if any(request.url.path.startswith(path) for path in skip_paths):
            return True

        # Skip for WebSocket connections
        if request.url.path.startswith("/ws/"):
            return True

        return False

    def _validate_csrf_token(self, request: Request) -> bool:
        """Validate CSRF token using double-submit cookie pattern."""
        try:
            # Get token from header
            header_token = request.headers.get(self.header_name)
            if not header_token:
                logger.debug("No CSRF token in header")
                return False

            # Get token from cookie
            cookie_token = request.cookies.get(self.cookie_name)
            if not cookie_token:
                logger.debug("No CSRF token in cookie")
                return False

            # Validate token format
            if not self._is_valid_token_format(header_token) or not self._is_valid_token_format(cookie_token):
                logger.debug("Invalid CSRF token format")
                return False

            # Compare tokens (double-submit pattern)
            if not hmac.compare_digest(header_token, cookie_token):
                logger.debug("CSRF tokens don't match")
                return False

            # Verify token signature
            if not self._verify_token_signature(header_token):
                logger.debug("CSRF token signature invalid")
                return False

            return True

        except Exception as e:
            logger.error(f"CSRF validation error: {e}")
            return False

    def _is_valid_token_format(self, token: str) -> bool:
        """Check if token has valid format."""
        if not token or len(token) != 64:  # 32 bytes = 64 hex chars
            return False

        try:
            # Check if it's valid hex
            bytes.fromhex(token)
            return True
        except ValueError:
            return False

    def _verify_token_signature(self, token: str) -> bool:
        """Verify token signature."""
        try:
            # Extract signature and payload
            if len(token) != 64:
                return False

            payload = token[:32]  # First 32 chars
            signature = token[32:]  # Last 32 chars

            # Verify signature
            expected_signature = hmac.new(
                self.secret_key,
                payload.encode(),
                hashlib.sha256
            ).hexdigest()[:32]

            return hmac.compare_digest(signature, expected_signature)
        except Exception:
            return False

    def _set_csrf_cookie(self, response: Response):
        """Set CSRF token cookie."""
        try:
            token = self._generate_csrf_token()
            response.set_cookie(
                key=self.cookie_name,
                value=token,
                max_age=self.cookie_max_age,
                secure=self.cookie_secure,
                httponly=self.cookie_httponly,
                samesite=self.cookie_samesite,
                path="/"
            )
        except Exception as e:
            logger.error(f"Failed to set CSRF cookie: {e}")

    def _generate_csrf_token(self) -> str:
        """Generate a new CSRF token."""
        try:
            # Generate random payload
            payload = secrets.token_hex(16)  # 16 bytes = 32 hex chars

            # Generate signature
            signature = hmac.new(
                self.secret_key,
                payload.encode(),
                hashlib.sha256
            ).hexdigest()[:32]  # First 32 chars of signature

            return payload + signature
        except Exception as e:
            logger.error(f"Failed to generate CSRF token: {e}")
            return secrets.token_hex(32)  # Fallback to simple random token


def get_csrf_token_from_request(request: Request) -> Optional[str]:
    """Extract CSRF token from request for frontend use."""
    return request.cookies.get("csrf_token")


def create_csrf_protection_middleware(secret_key: str) -> CSRFProtectionMiddleware:
    """Create CSRF protection middleware instance."""
    return CSRFProtectionMiddleware(None, secret_key)
