"""Advanced input validation middleware for API requests.

This module provides comprehensive request validation including:
- Request size limits
- Content type validation
- Parameter sanitization
- SQL injection prevention
- XSS protection
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Comprehensive input validation middleware."""

    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_request_size = max_request_size
        self.suspicious_patterns = [
            r"<script[^>]*>.*?</script>",  # Script tags
            r"javascript:",  # JavaScript protocol
            r"on\w+\s*=",  # Event handlers
            r"(\b(union|select|insert|update|delete|drop|create|alter)\b)",  # SQL keywords
            r"(\bor\b\s+\d+\s*=\s*\d+)",  # SQL injection patterns
            r"(\band\b\s+\d+\s*=\s*\d+)",  # SQL injection patterns
        ]
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_patterns
        ]

    async def dispatch(self, request: Request, call_next):
        """Process request through validation pipeline."""
        try:
            # 1. Check request size
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_request_size:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "Request too large",
                        "max_size": self.max_request_size,
                    },
                )

            # 2. Validate content type for POST/PUT requests
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "")
                if not self._is_valid_content_type(content_type):
                    return JSONResponse(
                        status_code=415, content={"error": "Unsupported content type"}
                    )

            # 3. Validate and sanitize query parameters
            if request.query_params:
                sanitized_params = self._sanitize_params(dict(request.query_params))
                if sanitized_params != dict(request.query_params):
                    logger.warning(
                        f"Suspicious query parameters detected: {request.url}"
                    )
                    return JSONResponse(
                        status_code=400, content={"error": "Invalid query parameters"}
                    )

            # 4. Validate request body for JSON requests
            if request.method in [
                "POST",
                "PUT",
                "PATCH",
            ] and "application/json" in request.headers.get("content-type", ""):
                try:
                    body = await request.body()
                    if body:
                        json_data = json.loads(body.decode())
                        sanitized_data = self._sanitize_json_data(json_data)
                        if sanitized_data != json_data:
                            logger.warning(
                                f"Suspicious JSON data detected: {request.url}"
                            )
                            return JSONResponse(
                                status_code=400,
                                content={"error": "Invalid request data"},
                            )
                except json.JSONDecodeError:
                    return JSONResponse(
                        status_code=400, content={"error": "Invalid JSON format"}
                    )

            # 5. Add request metadata for tracking
            request.state.validation_passed = True
            request.state.request_id = self._generate_request_id()

            response = await call_next(request)

            # 6. Add security headers to response
            response.headers["X-Request-ID"] = request.state.request_id
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"

            return response

        except Exception as e:
            logger.error(f"Validation middleware error: {e}")
            return JSONResponse(
                status_code=500, content={"error": "Internal validation error"}
            )

    def _is_valid_content_type(self, content_type: str) -> bool:
        """Validate content type."""
        valid_types = [
            "application/json",
            "multipart/form-data",
            "application/x-www-form-urlencoded",
            "text/plain",
        ]
        return any(valid_type in content_type for valid_type in valid_types)

    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize query parameters."""
        sanitized = {}
        for key, value in params.items():
            if isinstance(value, str):
                if self._contains_suspicious_content(value):
                    return {}  # Return empty dict to indicate sanitization failure
                sanitized[key] = self._basic_sanitize(value)
            else:
                sanitized[key] = value
        return sanitized

    def _sanitize_json_data(self, data: Any) -> Any:
        """Recursively sanitize JSON data."""
        if isinstance(data, dict):
            return {key: self._sanitize_json_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_json_data(item) for item in data]
        elif isinstance(data, str):
            if self._contains_suspicious_content(data):
                return None  # Return None to indicate sanitization failure
            return self._basic_sanitize(data)
        else:
            return data

    def _contains_suspicious_content(self, text: str) -> bool:
        """Check for suspicious patterns in text."""
        return any(pattern.search(text) for pattern in self.compiled_patterns)

    def _basic_sanitize(self, text: str) -> str:
        """Basic text sanitization."""
        # Remove null bytes and control characters
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        # Limit length
        if len(text) > 10000:  # 10KB limit per field
            text = text[:10000]
        return text.strip()

    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        import uuid

        return str(uuid.uuid4())[:8]
