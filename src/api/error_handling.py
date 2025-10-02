import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = structlog.get_logger(__name__)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Global handler for HTTP exceptions to ensure consistent JSON error responses.
    """
    logger.error(
        "HTTP Exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
