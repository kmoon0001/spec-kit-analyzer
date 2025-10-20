"""Enhanced logging configuration with structured logging and performance monitoring.

This module provides:
- Structured logging with JSON format
- Performance monitoring
- Request/response logging
- Error tracking and alerting
- Log rotation and management
"""

import json
import logging
import logging.handlers
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from structlog.stdlib import LoggerFactory


class PerformanceLogger:
    """Performance monitoring logger."""

    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)
        self._start_times: Dict[str, float] = {}

    def start_timer(self, operation: str) -> None:
        """Start timing an operation."""
        self._start_times[operation] = time.time()

    def end_timer(self, operation: str, **context) -> float:
        """End timing an operation and log the duration."""
        if operation not in self._start_times:
            self.logger.warning(f"Timer for '{operation}' was not started")
            return 0.0

        duration = time.time() - self._start_times[operation]
        del self._start_times[operation]

        self.logger.info(
            f"Operation '{operation}' completed",
            extra={
                "operation": operation,
                "duration_ms": round(duration * 1000, 2),
                "duration_seconds": round(duration, 3),
                **context,
            },
        )

        return duration

    def log_metric(
        self, metric_name: str, value: float, unit: str = "", **context
    ) -> None:
        """Log a performance metric."""
        self.logger.info(
            f"Metric: {metric_name}",
            extra={
                "metric_name": metric_name,
                "metric_value": value,
                "metric_unit": unit,
                **context,
            },
        )


class RequestLogger:
    """Request/response logging."""

    def __init__(self, logger_name: str = "requests"):
        self.logger = logging.getLogger(logger_name)

    def log_request(
        self,
        method: str,
        path: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        **context,
    ) -> None:
        """Log incoming request."""
        self.logger.info(
            f"Request: {method} {path}",
            extra={
                "event_type": "request",
                "method": method,
                "path": path,
                "user_id": user_id,
                "ip_address": ip_address,
                **context,
            },
        )

    def log_response(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[int] = None,
        **context,
    ) -> None:
        """Log response."""
        self.logger.info(
            f"Response: {method} {path} -> {status_code}",
            extra={
                "event_type": "response",
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "user_id": user_id,
                **context,
            },
        )


class ErrorTracker:
    """Enhanced error tracking and alerting."""

    def __init__(self, logger_name: str = "errors"):
        self.logger = logging.getLogger(logger_name)
        self._error_counts: Dict[str, int] = {}

    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Log an error with context."""
        error_key = f"{type(error).__name__}:{str(error)[:100]}"
        self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1

        self.logger.error(
            f"Error: {type(error).__name__}",
            extra={
                "event_type": "error",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "error_count": self._error_counts[error_key],
                "user_id": user_id,
                "request_id": request_id,
                "context": context or {},
            },
            exc_info=True,
        )

        # Alert on repeated errors
        if self._error_counts[error_key] >= 5:
            self.logger.critical(
                f"Repeated error alert: {error_key}",
                extra={
                    "event_type": "error_alert",
                    "error_key": error_key,
                    "count": self._error_counts[error_key],
                    "threshold": 5,
                },
            )

    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics."""
        return self._error_counts.copy()


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in {
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "lineno",
                    "funcName",
                    "created",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "processName",
                    "process",
                    "getMessage",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                }:
                    log_entry[key] = value

        # Add exception info
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def setup_enhanced_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_file_size_mb: int = 10,
    backup_count: int = 5,
    enable_json: bool = False,
    enable_console: bool = True,
) -> None:
    """Setup enhanced logging configuration."""

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))

        if enable_json:
            console_handler.setFormatter(JSONFormatter())
        else:
            console_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(console_formatter)

        root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))

        if enable_json:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)

        root_logger.addHandler(file_handler)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_performance_logger() -> PerformanceLogger:
    """Get performance logger instance."""
    return PerformanceLogger()


def get_request_logger() -> RequestLogger:
    """Get request logger instance."""
    return RequestLogger()


def get_error_tracker() -> ErrorTracker:
    """Get error tracker instance."""
    return ErrorTracker()


# Initialize enhanced logging
def initialize_logging() -> None:
    """Initialize enhanced logging system."""
    from src.core.enhanced_config import get_enhanced_settings

    settings = get_enhanced_settings()

    setup_enhanced_logging(
        log_level=settings.logging.level,
        log_file="logs/app.log" if settings.logging.file_enabled else None,
        max_file_size_mb=settings.logging.max_file_size_mb,
        backup_count=settings.logging.backup_count,
        enable_json=settings.is_production(),
        enable_console=settings.logging.console_enabled,
    )

    logger = logging.getLogger(__name__)
    logger.info("Enhanced logging system initialized")


# Global instances
_performance_logger = PerformanceLogger()
_request_logger = RequestLogger()
_error_tracker = ErrorTracker()


def get_loggers():
    """Get all logger instances."""
    return {
        "performance": _performance_logger,
        "requests": _request_logger,
        "errors": _error_tracker,
    }
