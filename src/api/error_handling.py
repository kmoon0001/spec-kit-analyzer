from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Any

class ErrorDetail(BaseModel):
    """Provides a detailed, machine-readable error code and message."""
    code: str = Field(..., description="A unique, machine-readable error code.", example="item_not_found")
    message: str = Field(..., description="A human-readable message providing context about the error.", example="The requested item could not be found.")

class ErrorResponse(BaseModel):
    """Standardized error response payload for the API."""
    status_code: int = Field(..., description="The HTTP status code.", example=404)
    error: ErrorDetail
    details: Optional[Any] = Field(None, description="Optional field for additional error details, such as validation errors.", example={"field": "name", "error": "must not be empty"})

async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler to standardize all API error responses.
    """
    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        if isinstance(exc.detail, dict) and 'code' in exc.detail and 'message' in exc.detail:
            error_detail = ErrorDetail(code=exc.detail['code'], message=exc.detail['message'])
            additional_details = exc.detail.get('details')
        else:
            # Fallback for standard HTTPException details (strings)
            error_detail = ErrorDetail(code="generic_error", message=str(exc.detail))
            additional_details = None
    else:
        # Handle non-HTTP exceptions (i.e., server errors)
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_detail = ErrorDetail(
            code="internal_server_error",
            message="An unexpected internal server error occurred."
        )
        additional_details = str(exc) # For debugging, not ideal for production

    error_response = ErrorResponse(
        status_code=status_code,
        error=error_detail,
        details=additional_details
    )

    return JSONResponse(
        status_code=status_code,
        content=error_response.dict(),
    )