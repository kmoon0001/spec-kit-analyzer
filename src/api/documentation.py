"""
API Documentation configuration and setup.
Provides comprehensive API documentation with examples and security schemes.
"""

import logging
from typing import Dict, Any
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

logger = logging.getLogger(__name__)

# Configuration for documentation features
DOCUMENTATION_CONFIG = {
    "enable_swagger": True,
    "enable_redoc": True,
    "enable_custom_docs": True,
    "include_examples": True,
    "include_security_info": True,
}


def setup_api_documentation(app: FastAPI) -> None:
    """
    Setup comprehensive API documentation for the application.

    Args:
        app: FastAPI application instance
    """
    # Set custom OpenAPI schema
    def custom_openapi():
        return create_custom_openapi(app)
    setattr(app, 'openapi', custom_openapi)

    # Add custom documentation endpoint
    @app.get("/docs/api", include_in_schema=False)
    async def get_api_documentation():
        """Get comprehensive API documentation as HTML."""
        return generate_api_documentation_html()

    logger.info("API documentation setup completed")


def create_custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """Generate enhanced OpenAPI schema with examples and security."""
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title="Therapy Compliance Analyzer API",
        version="1.0.0",
        description="Comprehensive API for clinical documentation compliance analysis",
        routes=app.routes,
    )

    # Add security schemes
    _add_security_schemes(schema)

    # Add common examples
    _add_common_examples(schema)

    # Add response examples
    _add_response_examples(schema)

    app.openapi_schema = schema
    return schema


def _add_security_schemes(schema: Dict[str, Any]) -> None:
    """Add security scheme definitions."""
    if "components" not in schema:
        schema["components"] = {}

    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /auth/login endpoint",
        }
    }

    # Add security requirements to protected endpoints
    protected_paths = ["/api/analysis/", "/api/dashboard/", "/api/admin/"]

    if "paths" in schema:
        for path_url, path_item in schema["paths"].items():
            if any(protected in path_url for protected in protected_paths):
                for _, operation in path_item.items():
                    if isinstance(operation, dict):
                        operation["security"] = [{"BearerAuth": []}]


def _add_common_examples(schema: Dict[str, Any]) -> None:
    """Add common request/response examples for API endpoints."""
    if "components" not in schema:
        schema["components"] = {}

    if "examples" not in schema["components"]:
        schema["components"]["examples"] = {}

    # Common examples
    common_examples = {
        "LoginRequest": {
            "summary": "Example login request",
            "description": "Standard user authentication",
            "value": {
                "username": "therapist@clinic.com",
                "password": "secure_password",
            },
        },
        "LoginResponse": {
            "summary": "Successful login response",
            "description": "JWT token obtained for authentication",
            "value": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
            },
        },
        "ComplianceReport": {
            "summary": "Example compliance analysis report",
            "description": "Document analysis results with findings",
            "value": {
                "document_name": "progress_note_2024_01_15.pdf",
                "analysis_date": "2024-01-15T10:30:00Z",
                "compliance_score": 87.5,
                "risk_distribution": {"High": 2, "Medium": 5, "Low": 12},
            },
        },
    }

    schema["components"]["examples"].update(common_examples)


def _add_response_examples(schema: Dict[str, Any]) -> None:
    """Add detailed response examples for API endpoints."""
    # Add examples for specific endpoints
    if "paths" not in schema:
        return

    # Example for analysis endpoint
    analyze_path = "/api/analysis/analyze"
    if analyze_path in schema["paths"]:
        if "post" in schema["paths"][analyze_path]:
            schema["paths"][analyze_path]["post"]["requestBody"] = {
                "content": {
                    "multipart/form-data": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "file": {
                                    "type": "string",
                                    "format": "binary",
                                    "description": "Document file to analyze (PDF, DOCX, or TXT)",
                                },
                                "rubric_id": {
                                    "type": "string",
                                    "description": "ID of compliance rubric to use",
                                    "example": "pt_compliance_v1",
                                },
                            },
                        }
                    }
                }
            }


def generate_api_documentation_html() -> str:
    """Generate comprehensive API documentation as HTML string."""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Therapy Compliance Analyzer API Documentation</title>
        <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { background: #f4f4f4; padding: 20px; margin: 20px 0; border-radius: 5px; }
        .endpoint { margin: 20px 0; padding: 15px; border-left: 4px solid #007cba; }
        .method { font-weight: bold; color: #007cba; }
        .code { background: #f9f9f9; padding: 10px; border-radius: 3px; font-family: monospace; }
        .example { background: #e8f5e8; padding: 10px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Therapy Compliance Analyzer API</h1>
            <p>Comprehensive API for clinical documentation compliance analysis with Medicare and regulatory guidelines.</p>
        </div>

        <h2>Authentication</h2>
        <div class="endpoint">
            <h3><span class="method">POST</span> /auth/login</h3>
            <p>Authenticate user and obtain JWT token for API access.</p>
            <div class="code">
                {
                    "username": "therapist@example.com",
                    "password": "password"
                }
            </div>
        </div>

        <h2>Document Analysis</h2>
        <div class="endpoint">
            <h3><span class="method">POST</span> /api/analysis/analyze</h3>
            <p>Upload and analyze a clinical document for compliance issues.</p>
            <p><strong>Headers:</strong> Authorization: Bearer {token}</p>
            <p><strong>Content-Type:</strong> multipart/form-data</p>
            <div class="code">
                file: [document file]<br>
                rubric_id: "pt_compliance_v1"
            </div>
        </div>

        <h2>Dashboard & Analytics</h2>
        <div class="endpoint">
            <h3><span class="method">GET</span> /api/dashboard/trends</h3>
            <p>Get compliance trends and analytics data.</p>
            <p><strong>Parameters:</strong> days (optional), document_type (optional)</p>
        </div>

        <h2>Performance Settings</h2>
        <div class="endpoint">
            <h3><span class="method">GET</span> /api/system/performance</h3>
            <p>Get current performance configuration and system status.</p>
        </div>

        <div class="endpoint">
            <h3><span class="method">POST</span> /api/system/performance</h3>
            <p>Update performance settings based on hardware capabilities.</p>
            <div class="code">
                {
                    "profile": "balanced",
                    "use_gpu": true,
                    "cache_memory_mb": 2048
                }
            </div>
        </div>

        <h2>Rate Limiting</h2>
        <p>API endpoints are rate-limited to ensure system stability. See individual endpoint documentation for specific limits.</p>

        <h2>Error Handling</h2>
        <p>All endpoints return structured error responses with appropriate HTTP status codes and detailed error information.</p>
        <div class="code">
            {
                "error": "ERROR_CODE",
                "detail": "Detailed error information",
            }
        </div>
    </body>
    </html>
    """

    return html_template


def is_documentation_feature_enabled(feature: str) -> bool:
    """Check if a documentation feature is enabled."""
    return DOCUMENTATION_CONFIG.get(feature, False)
