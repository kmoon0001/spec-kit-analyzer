"""Security Middleware for Clinical Compliance Analysis API.

This module provides comprehensive security middleware including:
- Request validation and sanitization
- Rate limiting and DDoS protection
- Threat detection and prevention
- Security logging and monitoring
"""

import logging
import time
from datetime import datetime
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.advanced_security_system import security_system, SecurityLevel, ThreatType

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Advanced security middleware for API protection."""

    def __init__(self, app, enable_threat_detection: bool = True):
        super().__init__(app)
        self.enable_threat_detection = enable_threat_detection

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security middleware."""
        start_time = time.time()

        try:
            # Get client information
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")

            # Check if IP is blocked
            if security_system.is_blocked(client_ip):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "IP address is temporarily blocked"}
                )

            # Rate limiting
            if not security_system.check_rate_limit(client_ip):
                security_system.log_security_event(
                    event_type="rate_limit_exceeded",
                    severity=SecurityLevel.MEDIUM,
                    description=f"Rate limit exceeded for IP {client_ip}",
                    ip_address=client_ip,
                    user_agent=user_agent
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded"}
                )

            # Threat detection
            if self.enable_threat_detection:
                threats = await self._detect_threats(request)
                if threats:
                    security_system.log_security_event(
                        event_type="threat_detected",
                        severity=SecurityLevel.HIGH,
                        description=f"Threats detected: {[t.value for t in threats]}",
                        ip_address=client_ip,
                        user_agent=user_agent,
                        details={"threats": [t.value for t in threats]}
                    )
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": "Potential security threat detected"}
                    )

            # Process request
            response = await call_next(request)

            # Log successful request
            processing_time = time.time() - start_time
            if processing_time > 5.0:  # Log slow requests
                security_system.log_security_event(
                    event_type="slow_request",
                    severity=SecurityLevel.LOW,
                    description=f"Slow request detected: {processing_time:.2f}s",
                    ip_address=client_ip,
                    user_agent=user_agent,
                    details={"processing_time": processing_time, "path": request.url.path}
                )

            return response

        except Exception as e:
            # Log security-related errors
            security_system.log_security_event(
                event_type="security_error",
                severity=SecurityLevel.HIGH,
                description=f"Security middleware error: {str(e)}",
                ip_address=client_ip,
                user_agent=user_agent
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal security error"}
            )

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to direct connection
        return request.client.host if request.client else "unknown"

    async def _detect_threats(self, request: Request) -> list[ThreatType]:
        """Detect threats in the request."""
        threats = []

        # Get request data
        request_data = {}

        # Add query parameters
        if request.query_params:
            request_data.update(dict(request.query_params))

        # Add path parameters
        if request.path_params:
            request_data.update(request.path_params)

        # Add headers (sanitized)
        headers_data = {}
        for key, value in request.headers.items():
            if key.lower() not in ['authorization', 'cookie']:  # Skip sensitive headers
                headers_data[key] = value
        request_data['headers'] = headers_data

        # Detect threats
        threats = security_system.detect_threats(request_data)

        return threats


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Authentication and authorization middleware."""

    def __init__(self, app, require_auth_paths: Optional[list[str]] = None):
        super().__init__(app)
        self.require_auth_paths = require_auth_paths or [
            "/api/analysis",
            "/api/dashboard",
            "/api/feedback",
            "/api/education",
            "/api/analytics"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process authentication for protected routes."""

        # Check if path requires authentication
        if not self._requires_auth(request.url.path):
            return await call_next(request)

        # Get authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid authorization header"}
            )

        # Extract token
        token = auth_header.split(" ")[1]

        # Validate token
        payload = security_system.validate_token(token)
        if not payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"}
            )

        # Add user info to request state
        request.state.user_id = payload.get("user_id")
        request.state.token_payload = payload

        return await call_next(request)

    def _requires_auth(self, path: str) -> bool:
        """Check if path requires authentication."""
        return any(path.startswith(auth_path) for auth_path in self.require_auth_paths)


class DataProtectionMiddleware(BaseHTTPMiddleware):
    """Data protection and privacy middleware."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process data protection for requests and responses."""

        # Sanitize request data
        if hasattr(request, '_body'):
            # This would need to be implemented based on your specific needs
            pass

        # Process response
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response


def setup_security_middleware(app):
    """Setup all security middleware."""

    # Add security middleware
    app.add_middleware(SecurityMiddleware, enable_threat_detection=True)
    app.add_middleware(AuthenticationMiddleware)
    app.add_middleware(DataProtectionMiddleware)

    logger.info("Security middleware setup completed")
