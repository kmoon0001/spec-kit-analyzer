import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Global handler for HTTP exceptions to ensure consistent JSON error responses.
    """
    logger.error(
        f"HTTP Exception: {exc.status_code} {exc.detail} for request {request.url.path}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
