"""Centralized Logging and Time Utilities for Clinical Compliance Analysis.

This module provides centralized logging configuration, time utilities, and
common patterns used throughout the application using expert practices.

Features:
- Centralized logging configuration with structured logging
- Time utilities with timezone support
- Performance timing decorators
- Logging decorators for function tracing
- Comprehensive error logging
- Audit trail logging for compliance
"""

import asyncio
import functools
import logging
import logging.config
import time
import traceback
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, ParamSpec
import json
import sys
from contextlib import contextmanager, asynccontextmanager
from dataclasses import dataclass, field
import threading
from collections import defaultdict, deque

# Type definitions
T = TypeVar('T')
P = ParamSpec('P')

# Logging levels
class LogLevel(Enum):
    """Standardized logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: datetime
    level: str
    logger_name: str
    message: str
    module: str
    function: str
    line_number: int
    thread_id: int
    process_id: int
    extra_data: Dict[str, Any] = field(default_factory=dict)
    exception_info: Optional[str] = None


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created, tz=timezone.utc),
            level=record.levelname,
            logger_name=record.name,
            message=record.getMessage(),
            module=record.module,
            function=record.funcName,
            line_number=record.lineno,
            thread_id=record.thread,
            process_id=record.process,
            extra_data=getattr(record, 'extra_data', {}),
            exception_info=self.formatException(record.exc_info) if record.exc_info else None
        )

        return json.dumps({
            'timestamp': log_entry.timestamp.isoformat(),
            'level': log_entry.level,
            'logger': log_entry.logger_name,
            'message': log_entry.message,
            'module': log_entry.module,
            'function': log_entry.function,
            'line': log_entry.line_number,
            'thread_id': log_entry.thread_id,
            'process_id': log_entry.process_id,
            'extra': log_entry.extra_data,
            'exception': log_entry.exception_info
        }, default=str)


class PerformanceTracker:
    """Performance tracking for functions and operations."""

    def __init__(self, max_entries: int = 1000):
        self.max_entries = max_entries
        self.performance_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_entries))
        self.lock = threading.RLock()

    def record_timing(self, operation: str, duration_ms: float, metadata: Optional[Dict[str, Any]] = None):
        """Record timing for an operation."""
        with self.lock:
            entry = {
                'timestamp': datetime.now(timezone.utc),
                'duration_ms': duration_ms,
                'metadata': metadata or {}
            }
            self.performance_data[operation].append(entry)

    def get_statistics(self, operation: str) -> Dict[str, Any]:
        """Get performance statistics for an operation."""
        with self.lock:
            if operation not in self.performance_data or not self.performance_data[operation]:
                return {'count': 0}

            durations = [entry['duration_ms'] for entry in self.performance_data[operation]]

            return {
                'count': len(durations),
                'min_ms': min(durations),
                'max_ms': max(durations),
                'avg_ms': sum(durations) / len(durations),
                'p50_ms': sorted(durations)[len(durations) // 2],
                'p95_ms': sorted(durations)[int(len(durations) * 0.95)],
                'p99_ms': sorted(durations)[int(len(durations) * 0.99)]
            }

    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all operations."""
        return {operation: self.get_statistics(operation)
                for operation in self.performance_data.keys()}


class AuditLogger:
    """Audit logger for compliance tracking."""

    def __init__(self, logger_name: str = 'audit'):
        self.logger = logging.getLogger(logger_name)
        self.audit_events: List[Dict[str, Any]] = []
        self.lock = threading.RLock()

    def log_user_action(
        self,
        user_id: int,
        action: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True
    ):
        """Log user action for audit trail."""
        audit_event = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'success': success,
            'details': details or {},
            'ip_address': getattr(threading.current_thread(), 'ip_address', None)
        }

        with self.lock:
            self.audit_events.append(audit_event)

        # Log to file
        self.logger.info(
            "User action: %s by user %d on %s - %s",
            action, user_id, resource, "SUCCESS" if success else "FAILED",
            extra={'audit_event': audit_event}
        )

    def log_system_event(
        self,
        event_type: str,
        description: str,
        severity: str = 'INFO',
        details: Optional[Dict[str, Any]] = None
    ):
        """Log system event for audit trail."""
        audit_event = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event_type': event_type,
            'description': description,
            'severity': severity,
            'details': details or {}
        }

        with self.lock:
            self.audit_events.append(audit_event)

        # Log to appropriate level
        log_level = getattr(logging, severity.upper(), logging.INFO)
        self.logger.log(
            log_level,
            "System event: %s - %s",
            event_type, description,
            extra={'audit_event': audit_event}
        )

    def get_audit_trail(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[int] = None,
        event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get filtered audit trail."""
        with self.lock:
            filtered_events = self.audit_events.copy()

        # Apply filters
        if start_time:
            filtered_events = [
                event for event in filtered_events
                if datetime.fromisoformat(event['timestamp']) >= start_time
            ]

        if end_time:
            filtered_events = [
                event for event in filtered_events
                if datetime.fromisoformat(event['timestamp']) <= end_time
            ]

        if user_id is not None:
            filtered_events = [
                event for event in filtered_events
                if event.get('user_id') == user_id
            ]

        if event_type:
            filtered_events = [
                event for event in filtered_events
                if event.get('event_type') == event_type
            ]

        return filtered_events


class TimeUtils:
    """Centralized time utilities with timezone support."""

    @staticmethod
    def now() -> datetime:
        """Get current UTC time."""
        return datetime.now(timezone.utc)

    @staticmethod
    def now_local() -> datetime:
        """Get current local time."""
        return datetime.now()

    @staticmethod
    def to_utc(dt: datetime) -> datetime:
        """Convert datetime to UTC."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def to_local(dt: datetime) -> datetime:
        """Convert UTC datetime to local time."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone()

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 1:
            return f"{seconds * 1000:.1f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

    @staticmethod
    def parse_duration(duration_str: str) -> timedelta:
        """Parse duration string to timedelta."""
        duration_str = duration_str.strip().lower()

        if duration_str.endswith('ms'):
            return timedelta(milliseconds=float(duration_str[:-2]))
        elif duration_str.endswith('s'):
            return timedelta(seconds=float(duration_str[:-1]))
        elif duration_str.endswith('m'):
            return timedelta(minutes=float(duration_str[:-1]))
        elif duration_str.endswith('h'):
            return timedelta(hours=float(duration_str[:-1]))
        elif duration_str.endswith('d'):
            return timedelta(days=float(duration_str[:-1]))
        else:
            # Assume seconds
            return timedelta(seconds=float(duration_str))


# Global instances
performance_tracker = PerformanceTracker()
audit_logger = AuditLogger()
time_utils = TimeUtils()


def setup_logging(
    log_level: str = 'INFO',
    log_file: Optional[str] = None,
    log_format: str = 'json',
    enable_audit: bool = True,
    enable_performance: bool = True
) -> None:
    """Setup centralized logging configuration."""

    # Create logs directory
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # Configure logging
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
            },
            'json': {
                '()': StructuredFormatter
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'detailed',
                'stream': 'ext://sys.stdout'
            }
        },
        'loggers': {
            '': {  # Root logger
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'audit': {
                'level': 'INFO',
                'handlers': [],
                'propagate': False
            },
            'performance': {
                'level': 'DEBUG',
                'handlers': [],
                'propagate': False
            }
        }
    }

    # Add file handler if specified
    if log_file:
        config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': log_format,
            'filename': str(log_dir / log_file),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5
        }

        # Add file handler to root logger
        config['loggers']['']['handlers'].append('file')

    # Add audit file handler
    if enable_audit:
        config['handlers']['audit_file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'json',
            'filename': str(log_dir / 'audit.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 10
        }

        config['loggers']['audit']['handlers'].append('audit_file')

    # Add performance file handler
    if enable_performance:
        config['handlers']['performance_file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'json',
            'filename': str(log_dir / 'performance.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5
        }

        config['loggers']['performance']['handlers'].append('performance_file')

    # Apply configuration
    logging.config.dictConfig(config)

    # Log setup completion
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized with level=%s, format=%s", log_level, log_format)


def get_logger(name: str) -> logging.Logger:
    """Get logger with standardized configuration."""
    return logging.getLogger(name)


def log_function_call(
    logger: Optional[logging.Logger] = None,
    level: int = logging.DEBUG,
    include_args: bool = True,
    include_result: bool = False,
    include_timing: bool = True
):
    """Decorator to log function calls with comprehensive information."""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            func_logger = logger or get_logger(func.__module__)
            start_time = time.time()

            # Log function entry
            log_data = {
                'function': func.__name__,
                'module': func.__module__,
                'args_count': len(args),
                'kwargs_count': len(kwargs)
            }

            if include_args and args:
                log_data['args'] = str(args)[:200]  # Truncate long args

            if include_args and kwargs:
                log_data['kwargs'] = str(kwargs)[:200]  # Truncate long kwargs

            func_logger.log(level, "Calling %s.%s", func.__module__, func.__name__, extra=log_data)

            try:
                result = func(*args, **kwargs)

                # Log function exit
                end_time = time.time()
                duration = end_time - start_time

                exit_data = {
                    'function': func.__name__,
                    'module': func.__module__,
                    'duration_ms': duration * 1000,
                    'success': True
                }

                if include_result:
                    exit_data['result'] = str(result)[:200]  # Truncate long results

                func_logger.log(level, "Completed %s.%s in %.2fms",
                              func.__module__, func.__name__, duration * 1000, extra=exit_data)

                # Record performance
                if include_timing:
                    performance_tracker.record_timing(
                        f"{func.__module__}.{func.__name__}",
                        duration * 1000,
                        {'args_count': len(args), 'kwargs_count': len(kwargs)}
                    )

                return result

            except Exception as e:
                # Log function error
                end_time = time.time()
                duration = end_time - start_time

                error_data = {
                    'function': func.__name__,
                    'module': func.__module__,
                    'duration_ms': duration * 1000,
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__
                }

                func_logger.error("Failed %s.%s in %.2fms: %s",
                                func.__module__, func.__name__, duration * 1000, str(e), extra=error_data)

                raise

        return wrapper
    return decorator


def log_async_function_call(
    logger: Optional[logging.Logger] = None,
    level: int = logging.DEBUG,
    include_args: bool = True,
    include_result: bool = False,
    include_timing: bool = True
):
    """Decorator to log async function calls with comprehensive information."""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            func_logger = logger or get_logger(func.__module__)
            start_time = time.time()

            # Log function entry
            log_data = {
                'function': func.__name__,
                'module': func.__module__,
                'args_count': len(args),
                'kwargs_count': len(kwargs),
                'async': True
            }

            if include_args and args:
                log_data['args'] = str(args)[:200]  # Truncate long args

            if include_args and kwargs:
                log_data['kwargs'] = str(kwargs)[:200]  # Truncate long kwargs

            func_logger.log(level, "Calling async %s.%s", func.__module__, func.__name__, extra=log_data)

            try:
                result = await func(*args, **kwargs)

                # Log function exit
                end_time = time.time()
                duration = end_time - start_time

                exit_data = {
                    'function': func.__name__,
                    'module': func.__module__,
                    'duration_ms': duration * 1000,
                    'success': True,
                    'async': True
                }

                if include_result:
                    exit_data['result'] = str(result)[:200]  # Truncate long results

                func_logger.log(level, "Completed async %s.%s in %.2fms",
                              func.__module__, func.__name__, duration * 1000, extra=exit_data)

                # Record performance
                if include_timing:
                    performance_tracker.record_timing(
                        f"{func.__module__}.{func.__name__}",
                        duration * 1000,
                        {'args_count': len(args), 'kwargs_count': len(kwargs), 'async': True}
                    )

                return result

            except Exception as e:
                # Log function error
                end_time = time.time()
                duration = end_time - start_time

                error_data = {
                    'function': func.__name__,
                    'module': func.__module__,
                    'duration_ms': duration * 1000,
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'async': True
                }

                func_logger.error("Failed async %s.%s in %.2fms: %s",
                                func.__module__, func.__name__, duration * 1000, str(e), extra=error_data)

                raise

        return wrapper
    return decorator


@contextmanager
def log_execution_time(operation: str, logger: Optional[logging.Logger] = None):
    """Context manager to log execution time."""
    func_logger = logger or get_logger(__name__)
    start_time = time.time()

    func_logger.debug("Starting operation: %s", operation)

    try:
        yield
    finally:
        duration = time.time() - start_time
        func_logger.debug("Completed operation: %s in %.2fms", operation, duration * 1000)

        # Record performance
        performance_tracker.record_timing(operation, duration * 1000)


@asynccontextmanager
async def log_async_execution_time(operation: str, logger: Optional[logging.Logger] = None):
    """Async context manager to log execution time."""
    func_logger = logger or get_logger(__name__)
    start_time = time.time()

    func_logger.debug("Starting async operation: %s", operation)

    try:
        yield
    finally:
        duration = time.time() - start_time
        func_logger.debug("Completed async operation: %s in %.2fms", operation, duration * 1000)

        # Record performance
        performance_tracker.record_timing(f"async_{operation}", duration * 1000)


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: int = logging.ERROR
):
    """Log error with comprehensive context information."""
    error_data = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'traceback': traceback.format_exc(),
        'context': context or {}
    }

    logger.log(level, "Error occurred: %s", str(error), extra=error_data)


def get_performance_statistics() -> Dict[str, Dict[str, Any]]:
    """Get comprehensive performance statistics."""
    return performance_tracker.get_all_statistics()


def get_audit_trail(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    user_id: Optional[int] = None,
    event_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get filtered audit trail."""
    return audit_logger.get_audit_trail(start_time, end_time, user_id, event_type)


# Initialize logging system
setup_logging(
    log_level='INFO',
    log_file='app.log',
    log_format='json',
    enable_audit=True,
    enable_performance=True
)
