"""Enhanced error context and reporting system.

Provides comprehensive error context including:
- Stack trace analysis
- Request context preservation
- Error categorization
- Performance impact tracking
- User-friendly error messages
- Error aggregation and reporting
"""

import asyncio
import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better organization."""

    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    AI_MODEL = "ai_model"
    NETWORK = "network"
    SYSTEM = "system"
    BUSINESS_LOGIC = "business_logic"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Comprehensive error context information."""

    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    request_context: Optional[Dict[str, Any]] = None
    user_context: Optional[Dict[str, Any]] = None
    performance_impact: Optional[Dict[str, Any]] = None
    suggestions: List[str] = field(default_factory=list)


class ErrorContextManager:
    """Manages error context collection and reporting."""

    def __init__(self):
        self.error_patterns = {
            "database": [
                "sqlalchemy",
                "database",
                "connection",
                "query",
                "transaction",
            ],
            "ai_model": [
                "llm",
                "model",
                "inference",
                "transformers",
                "torch",
                "tensor",
            ],
            "authentication": [
                "jwt",
                "token",
                "auth",
                "login",
                "password",
                "credential",
            ],
            "validation": ["validation", "invalid", "required", "format", "constraint"],
            "network": ["connection", "timeout", "network", "http", "request"],
        }

        self.error_suggestions = {
            ErrorCategory.DATABASE: [
                "Check database connectivity",
                "Verify database credentials",
                "Review query syntax",
                "Check database server status",
            ],
            ErrorCategory.AI_MODEL: [
                "Verify AI model is loaded",
                "Check model file integrity",
                "Ensure sufficient memory",
                "Try using mock AI mode",
            ],
            ErrorCategory.AUTHENTICATION: [
                "Check JWT token validity",
                "Verify user credentials",
                "Ensure proper authentication headers",
                "Check token expiration",
            ],
            ErrorCategory.VALIDATION: [
                "Review input data format",
                "Check required fields",
                "Validate data types",
                "Ensure proper encoding",
            ],
            ErrorCategory.NETWORK: [
                "Check network connectivity",
                "Verify external service status",
                "Review timeout settings",
                "Check firewall configuration",
            ],
        }

    def analyze_error(
        self, error: Exception, request: Optional[Request] = None
    ) -> ErrorContext:
        """Analyze an error and create comprehensive context."""
        import uuid

        error_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now(timezone.utc)

        # Determine error category
        category = self._categorize_error(error)

        # Determine severity
        severity = self._determine_severity(error, category)

        # Extract stack trace
        stack_trace = self._extract_stack_trace(error)

        # Collect request context
        request_context = self._collect_request_context(request) if request else None

        # Generate suggestions
        suggestions = self._generate_suggestions(category, error)

        # Create error context
        context = ErrorContext(
            error_id=error_id,
            timestamp=timestamp,
            severity=severity,
            category=category,
            message=str(error),
            details=self._extract_error_details(error),
            stack_trace=stack_trace,
            request_context=request_context,
            suggestions=suggestions,
        )

        return context

    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error based on type and message."""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        for category, patterns in self.error_patterns.items():
            if any(
                pattern in error_str or pattern in error_type for pattern in patterns
            ):
                return ErrorCategory(category)

        return ErrorCategory.UNKNOWN

    def _determine_severity(
        self, error: Exception, category: ErrorCategory
    ) -> ErrorSeverity:
        """Determine error severity based on type and context."""
        error_str = str(error).lower()

        # Critical errors
        if any(
            keyword in error_str
            for keyword in ["critical", "fatal", "system", "memory"]
        ):
            return ErrorSeverity.CRITICAL

        # High severity errors
        if category in [ErrorCategory.DATABASE, ErrorCategory.AI_MODEL]:
            return ErrorSeverity.HIGH

        # Medium severity errors
        if category in [ErrorCategory.AUTHENTICATION, ErrorCategory.AUTHORIZATION]:
            return ErrorSeverity.MEDIUM

        # Default to low severity
        return ErrorSeverity.LOW

    def _extract_stack_trace(self, error: Exception) -> str:
        """Extract and format stack trace."""
        try:
            return "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )
        except Exception:
            return "Unable to extract stack trace"

    def _collect_request_context(self, request: Request) -> Dict[str, Any]:
        """Collect relevant request context."""
        try:
            # Build headers with redaction of sensitive entries
            redacted_headers: Dict[str, Any] = {}
            sensitive = {"authorization", "cookie", "x-api-key"}
            for key, value in request.headers.items():
                if key.lower() in sensitive:
                    redacted_headers[key] = "***REDACTED***"
                else:
                    redacted_headers[key] = value

            return {
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": redacted_headers,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
        except Exception as e:
            logger.error(f"Failed to collect request context: {e}")
            return {"error": "Failed to collect request context"}

    def _extract_error_details(self, error: Exception) -> Dict[str, Any]:
        """Extract additional error details."""
        details = {
            "error_type": type(error).__name__,
            "error_module": getattr(error, "__module__", "unknown"),
        }

        # Add specific details for common error types
        if hasattr(error, "code"):
            details["error_code"] = error.code

        if hasattr(error, "status_code"):
            details["status_code"] = error.status_code

        if hasattr(error, "detail"):
            details["error_detail"] = error.detail

        return details

    def _generate_suggestions(
        self, category: ErrorCategory, error: Exception
    ) -> List[str]:
        """Generate helpful suggestions based on error category."""
        suggestions = self.error_suggestions.get(category, [])

        # Add specific suggestions based on error message
        error_str = str(error).lower()

        if "timeout" in error_str:
            suggestions.append("Consider increasing timeout values")

        if "memory" in error_str:
            suggestions.append("Check available system memory")

        if "permission" in error_str:
            suggestions.append("Verify file/directory permissions")

        return suggestions[:5]  # Limit to 5 suggestions

    def create_user_friendly_message(self, context: ErrorContext) -> str:
        """Create user-friendly error message."""
        base_messages = {
            ErrorCategory.VALIDATION: "There was an issue with the data you provided",
            ErrorCategory.AUTHENTICATION: "Authentication failed",
            ErrorCategory.AUTHORIZATION: "You don't have permission to perform this action",
            ErrorCategory.DATABASE: "A database error occurred",
            ErrorCategory.AI_MODEL: "AI processing failed",
            ErrorCategory.NETWORK: "Network connection issue",
            ErrorCategory.SYSTEM: "A system error occurred",
            ErrorCategory.BUSINESS_LOGIC: "Business logic error",
            ErrorCategory.UNKNOWN: "An unexpected error occurred",
        }

        return base_messages.get(context.category, "An error occurred")

    def log_error_context(self, context: ErrorContext):
        """Log error context with appropriate level."""
        log_data = {
            "error_id": context.error_id,
            "severity": context.severity.value,
            "category": context.category.value,
            "message": context.message,
            "timestamp": context.timestamp.isoformat(),
        }

        if context.request_context:
            log_data["request"] = context.request_context

        if context.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {context.message}", extra=log_data)
        elif context.severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {context.message}", extra=log_data)
        elif context.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {context.message}", extra=log_data)
        else:
            logger.info(f"Low severity error: {context.message}", extra=log_data)


# Global error context manager
error_context_manager = ErrorContextManager()


# Enhanced exception handler
async def enhanced_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Enhanced exception handler with comprehensive context."""
    try:
        # Analyze the error
        context = error_context_manager.analyze_error(exc, request)

        # Log the error
        error_context_manager.log_error_context(context)

        # Create user-friendly response
        user_message = error_context_manager.create_user_friendly_message(context)

        # Determine HTTP status code
        status_code = 500
        if isinstance(exc, HTTPException):
            status_code = exc.status_code
        elif context.category == ErrorCategory.VALIDATION:
            status_code = 400
        elif context.category == ErrorCategory.AUTHENTICATION:
            status_code = 401
        elif context.category == ErrorCategory.AUTHORIZATION:
            status_code = 403

        # Prepare response
        response_data = {
            "error": user_message,
            "error_id": context.error_id,
            "timestamp": context.timestamp.isoformat(),
            "suggestions": context.suggestions,
        }

        # Add debug information in development
        if request.app.debug:
            response_data["debug"] = {
                "message": context.message,
                "category": context.category.value,
                "severity": context.severity.value,
                "details": context.details,
            }

        return JSONResponse(status_code=status_code, content=response_data)

    except Exception as handler_error:
        logger.critical(f"Error handler failed: {handler_error}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "error_id": "handler_failed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )


# Utility decorator for error context
def with_error_context(func):
    """Decorator to add error context to function calls."""

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Try to extract request from args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            context = error_context_manager.analyze_error(e, request)
            error_context_manager.log_error_context(context)
            raise

    return wrapper
