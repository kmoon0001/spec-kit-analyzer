"""
API Documentation generator - Safe and stable implementation.
"""

import logging
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

logger = logging.getLogger(__name__)


def create_enhanced_openapi(app: FastAPI) -> dict[str, Any]:
    """Create enhanced OpenAPI documentation with examples."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Therapy Compliance Analyzer API",
        version="1.0.0",
        description="API for clinical documentation compliance analysis",
        routes=app.routes,
    )

    # Add security schemes
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def setup_documentation(app: FastAPI) -> None:
    """Setup API documentation with enhanced features."""

    def enhanced_openapi():
        return create_enhanced_openapi(app)

    app.openapi = enhanced_openapi
    logger.info("Enhanced API documentation configured")
