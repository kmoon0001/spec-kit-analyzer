"""Enhanced API documentation and OpenAPI schema.

Provides comprehensive API documentation including:
- Detailed endpoint descriptions
- Request/response schemas
- Example requests and responses
- Error code documentation
- Interactive API explorer
"""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def create_custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """Create enhanced OpenAPI schema with comprehensive documentation."""

    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Therapy Compliance Analyzer API",
        version="1.0.0",
        description="""
        # 🏥 Therapy Compliance Analyzer API

        A comprehensive API for analyzing clinical documentation compliance with Medicare and regulatory guidelines.

        ## Features

        - **Document Analysis**: Upload and analyze PDF, DOCX, and TXT documents
        - **Compliance Scoring**: AI-powered compliance analysis with confidence scores
        - **Real-time Progress**: WebSocket-based progress tracking
        - **User Management**: Secure authentication and user management
        - **Analytics**: Comprehensive reporting and analytics
        - **Health Monitoring**: System health and performance monitoring

        ## Authentication

        This API uses JWT-based authentication. Include the token in the Authorization header:

        ```
        Authorization: Bearer <your-jwt-token>
        ```

        ## Rate Limiting

        API requests are rate-limited to 100 requests per minute per IP address.

        ## Error Handling

        The API returns detailed error information including:
        - Error ID for tracking
        - User-friendly error messages
        - Suggested solutions
        - Debug information (in development mode)

        ## WebSocket Support

        Real-time updates are available via WebSocket connections for:
        - Analysis progress tracking
        - System health monitoring
        - Live log streaming
        """,
        routes=app.routes,
    )

    # Enhance the schema with additional information
    openapi_schema["info"]["contact"] = {
        "name": "Therapy Compliance Analyzer Support",
        "email": "support@therapyanalyzer.com",
        "url": "https://therapyanalyzer.com/support"
    }

    openapi_schema["info"]["license"] = {
        "name": "Proprietary",
        "url": "https://therapyanalyzer.com/license"
    }

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /auth/login endpoint"
        },
        "WebSocketAuth": {
            "type": "apiKey",
            "in": "query",
            "name": "token",
            "description": "JWT token for WebSocket authentication"
        }
    }

    # Add global security
    openapi_schema["security"] = [{"BearerAuth": []}]

    # Add server information
    openapi_schema["servers"] = [
        {
            "url": "http://127.0.0.1:8001",
            "description": "Development server"
        },
        {
            "url": "https://api.therapyanalyzer.com",
            "description": "Production server"
        }
    ]

    # Add tags for better organization
    openapi_schema["tags"] = [
        {
            "name": "Authentication",
            "description": "User authentication and authorization"
        },
        {
            "name": "Analysis",
            "description": "Document analysis and compliance checking"
        },
        {
            "name": "Dashboard",
            "description": "Analytics and reporting dashboard"
        },
        {
            "name": "Health",
            "description": "System health monitoring and diagnostics"
        },
        {
            "name": "WebSocket",
            "description": "Real-time communication endpoints"
        },
        {
            "name": "Admin",
            "description": "Administrative functions"
        },
        {
            "name": "Users",
            "description": "User management"
        },
        {
            "name": "Rubrics",
            "description": "Compliance rubric management"
        },
        {
            "name": "Habits",
            "description": "Habit tracking and analytics"
        },
        {
            "name": "Advanced Analytics",
            "description": "Advanced analytics and insights"
        },
        {
            "name": "Meta Analytics",
            "description": "Meta-level analytics and system metrics"
        },
        {
            "name": "Strictness",
            "description": "Analysis strictness configuration"
        }
    ]

    # Add common response schemas
    openapi_schema["components"]["schemas"].update({
        "ErrorResponse": {
            "type": "object",
            "properties": {
                "error": {
                    "type": "string",
                    "description": "User-friendly error message"
                },
                "error_id": {
                    "type": "string",
                    "description": "Unique error identifier for tracking"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Error timestamp"
                },
                "suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Suggested solutions"
                }
            },
            "required": ["error", "error_id", "timestamp"]
        },
        "SuccessResponse": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Success message"
                },
                "data": {
                    "type": "object",
                    "description": "Response data"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Response timestamp"
                }
            },
            "required": ["message", "timestamp"]
        },
        "AnalysisRequest": {
            "type": "object",
            "properties": {
                "document_name": {
                    "type": "string",
                    "description": "Name of the document"
                },
                "rubric": {
                    "type": "string",
                    "description": "Compliance rubric to use"
                },
                "strictness": {
                    "type": "string",
                    "enum": ["lenient", "standard", "strict"],
                    "description": "Analysis strictness level"
                },
                "discipline": {
                    "type": "string",
                    "enum": ["pt", "ot", "slp"],
                    "description": "Clinical discipline"
                }
            },
            "required": ["document_name", "rubric"]
        },
        "AnalysisResponse": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "Unique task identifier"
                },
                "status": {
                    "type": "string",
                    "enum": ["queued", "running", "completed", "failed"],
                    "description": "Analysis status"
                },
                "progress": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Progress percentage"
                },
                "message": {
                    "type": "string",
                    "description": "Status message"
                }
            },
            "required": ["task_id", "status"]
        }
    })

    # Add common responses
    openapi_schema["components"]["responses"] = {
        "UnauthorizedError": {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "error": "Authentication failed",
                        "error_id": "auth_001",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "suggestions": ["Check JWT token validity", "Ensure proper authentication headers"]
                    }
                }
            }
        },
        "ValidationError": {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "error": "There was an issue with the data you provided",
                        "error_id": "val_001",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "suggestions": ["Review input data format", "Check required fields"]
                    }
                }
            }
        },
        "ServerError": {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "error": "A system error occurred",
                        "error_id": "sys_001",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "suggestions": ["Try again later", "Contact support if issue persists"]
                    }
                }
            }
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema

def add_api_documentation_routes(app: FastAPI):
    """Add additional documentation routes."""

    @app.get("/docs/custom", include_in_schema=False)
    async def custom_docs():
        """Custom documentation page."""
        return {
            "message": "Custom API documentation",
            "endpoints": {
                "openapi": "/openapi.json",
                "swagger_ui": "/docs",
                "redoc": "/redoc",
                "health": "/health",
                "metrics": "/metrics"
            },
            "examples": {
                "analysis_request": {
                    "document_name": "Patient Progress Note",
                    "rubric": "pt_compliance_rubric",
                    "strictness": "standard",
                    "discipline": "pt"
                },
                "websocket_url": "ws://127.0.0.1:8001/ws/analysis/{task_id}?token={jwt_token}"
            }
        }

    @app.get("/api/status", include_in_schema=False)
    async def api_status():
        """API status endpoint."""
        return {
            "status": "operational",
            "version": "1.0.0",
            "timestamp": "2024-01-01T00:00:00Z",
            "features": [
                "Document Analysis",
                "Real-time Progress",
                "WebSocket Support",
                "Health Monitoring",
                "User Management",
                "Analytics Dashboard"
            ]
        }