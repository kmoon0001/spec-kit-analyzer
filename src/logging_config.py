import logging
import sys
import uuid

import structlog

# --- Correlation ID Middleware ---


class CorrelationIdMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        correlation_id = str(uuid.uuid4())

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                headers.append((b"X-Correlation-ID", correlation_id.encode()))
            await send(message)

        with structlog.contextvars.bound_contextvars(correlation_id=correlation_id):
            await self.app(scope, receive, send_wrapper)


# --- Structlog Configuration ---
# --- Structlog Configuration ---
# --- Structlog Configuration ---


def setup_logging():
    """Configures structured logging using structlog.
    This setup ensures that all logs are in JSON format, which is ideal for
    production environments and log analysis platforms.
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure the root logger to use structlog
    root_logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    # The JSON renderer will be used by structlog, so we can use a simple formatter here.
    # The key is to ensure the handler is added to the root logger.
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Supress noisy logs from uvicorn and other libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logger = structlog.get_logger("logging_setup")
    logger.info("Structured logging configured successfully.")


def configure_logging(level: str | int | None = None):
    """Backward-compatible alias for setup_logging with optional log level."""
    setup_logging()
    if level is not None:
        logging.getLogger().setLevel(level)
