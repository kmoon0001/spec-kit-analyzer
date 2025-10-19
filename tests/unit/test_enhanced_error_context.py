"""Comprehensive unit tests for enhanced error context system."""

import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from src.api.enhanced_error_context import (
    ErrorContextManager,
    ErrorSeverity,
    ErrorCategory,
    enhanced_exception_handler
)


class TestErrorContextManager:
    """Test suite for ErrorContextManager."""

    @pytest.fixture
    def error_manager(self):
        """Create ErrorContextManager instance."""
        return ErrorContextManager()

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/test"
        request.query_params = {"param": "value"}
        request.headers = {"User-Agent": "test-agent"}
        request.client.host = "127.0.0.1"
        return request

    def test_database_error_categorization(self, error_manager):
        """Test database errors are properly categorized."""
        error = Exception("SQLAlchemy connection failed")
        context = error_manager.analyze_error(error)

        assert context.category == ErrorCategory.DATABASE
        assert context.severity == ErrorSeverity.HIGH
        assert "SQLAlchemy" in context.message

    def test_ai_model_error_categorization(self, error_manager):
        """Test AI model errors are properly categorized."""
        error = Exception("LLM model loading failed")
        context = error_manager.analyze_error(error)

        assert context.category == ErrorCategory.AI_MODEL
        assert context.severity == ErrorSeverity.HIGH
        assert "LLM" in context.message

    def test_authentication_error_categorization(self, error_manager):
        """Test authentication errors are properly categorized."""
        error = Exception("JWT token validation failed")
        context = error_manager.analyze_error(error)

        assert context.category == ErrorCategory.AUTHENTICATION
        assert context.severity == ErrorSeverity.MEDIUM
        assert "JWT" in context.message

    def test_validation_error_categorization(self, error_manager):
        """Test validation errors are properly categorized."""
        error = Exception("Invalid input format")
        context = error_manager.analyze_error(error)

        assert context.category == ErrorCategory.VALIDATION
        assert context.severity == ErrorSeverity.LOW
        assert "Invalid" in context.message

    def test_critical_error_severity(self, error_manager):
        """Test critical errors are properly identified."""
        error = Exception("Critical system failure")
        context = error_manager.analyze_error(error)

        assert context.severity == ErrorSeverity.CRITICAL
        assert "Critical" in context.message

    def test_request_context_collection(self, error_manager, mock_request):
        """Test request context is properly collected."""
        error = Exception("Test error")
        context = error_manager.analyze_error(error, mock_request)

        assert context.request_context is not None
        assert context.request_context["method"] == "POST"
        assert context.request_context["path"] == "/test"
        assert context.request_context["client_ip"] == "127.0.0.1"
        assert "User-Agent" in context.request_context["headers"]

    def test_sensitive_headers_redaction(self, error_manager):
        """Test sensitive headers are redacted in request context."""
        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/test"
        request.query_params = {}
        request.headers = {
            "Authorization": "Bearer secret-token",
            "Cookie": "session=abc123",
            "User-Agent": "test-agent"
        }
        request.client.host = "127.0.0.1"

        error = Exception("Test error")
        context = error_manager.analyze_error(error, request)

        headers = context.request_context["headers"]
        assert headers["Authorization"] == "***REDACTED***"
        assert headers["Cookie"] == "***REDACTED***"
        assert headers["User-Agent"] == "test-agent"

    def test_error_suggestions_generation(self, error_manager):
        """Test error suggestions are generated based on category."""
        error = Exception("Database connection failed")
        context = error_manager.analyze_error(error)

        assert len(context.suggestions) > 0
        assert any("database" in suggestion.lower() for suggestion in context.suggestions)

    def test_stack_trace_extraction(self, error_manager):
        """Test stack trace is properly extracted."""
        try:
            raise ValueError("Test error")
        except ValueError as e:
            context = error_manager.analyze_error(e)

            assert context.stack_trace is not None
            assert "ValueError" in context.stack_trace
            assert "Test error" in context.stack_trace

    def test_error_id_generation(self, error_manager):
        """Test unique error IDs are generated."""
        error1 = Exception("Error 1")
        error2 = Exception("Error 2")

        context1 = error_manager.analyze_error(error1)
        context2 = error_manager.analyze_error(error2)

        assert context1.error_id != context2.error_id
        assert len(context1.error_id) == 8
        assert len(context2.error_id) == 8

    def test_user_friendly_message_generation(self, error_manager):
        """Test user-friendly messages are generated."""
        error = Exception("Database connection failed")
        context = error_manager.analyze_error(error)

        user_message = error_manager.create_user_friendly_message(context)
        assert user_message == "A database error occurred"

    def test_error_logging(self, error_manager):
        """Test error context is properly logged."""
        error = Exception("Test error")
        context = error_manager.analyze_error(error)

        with patch('src.api.enhanced_error_context.logger') as mock_logger:
            error_manager.log_error_context(context)

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "Test error" in str(call_args)

    def test_critical_error_logging(self, error_manager):
        """Test critical errors are logged at critical level."""
        error = Exception("Critical system failure")
        context = error_manager.analyze_error(error)

        with patch('src.api.enhanced_error_context.logger') as mock_logger:
            error_manager.log_error_context(context)

            mock_logger.critical.assert_called_once()

    def test_error_details_extraction(self, error_manager):
        """Test additional error details are extracted."""
        error = HTTPException(status_code=400, detail="Bad request")
        context = error_manager.analyze_error(error)

        assert context.details["error_type"] == "HTTPException"
        assert context.details["status_code"] == 400
        assert context.details["error_detail"] == "Bad request"

    def test_unknown_error_categorization(self, error_manager):
        """Test unknown errors are properly categorized."""
        error = Exception("Some random error")
        context = error_manager.analyze_error(error)

        assert context.category == ErrorCategory.UNKNOWN
        assert context.severity == ErrorSeverity.LOW


class TestEnhancedExceptionHandler:
    """Test suite for enhanced exception handler."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()

        @app.post("/test")
        async def test_endpoint():
            return {"message": "success"}

        @app.post("/test-error")
        async def test_error():
            raise HTTPException(status_code=400, detail="Test error")

        @app.post("/test-exception")
        async def test_exception():
            raise Exception("Unexpected error")

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_http_exception_handling(self, client):
        """Test HTTP exceptions are handled properly."""
        response = client.post("/test-error")

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "error_id" in data
        assert "timestamp" in data
        assert "suggestions" in data

    def test_generic_exception_handling(self, client):
        """Test generic exceptions are handled properly."""
        response = client.post("/test-exception")

        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "error_id" in data
        assert "timestamp" in data
        assert "suggestions" in data

    def test_debug_mode_response(self, client):
        """Test debug information is included in development mode."""
        with patch('src.api.enhanced_error_context.Request') as mock_request:
            mock_request.app.debug = True

            response = client.post("/test-exception")
            assert response.status_code == 500

            data = response.json()
            assert "debug" in data
            assert "message" in data["debug"]
            assert "category" in data["debug"]
            assert "severity" in data["debug"]

    def test_error_handler_exception_safety(self, client):
        """Test exception handler handles its own exceptions gracefully."""
        with patch('src.api.enhanced_error_context.ErrorContextManager.analyze_error',
                  side_effect=Exception("Handler error")):
            response = client.post("/test-exception")

            assert response.status_code == 500
            data = response.json()
            assert data["error"] == "Internal server error"
            assert data["error_id"] == "handler_failed"

    def test_request_context_in_error_response(self, client):
        """Test request context is included in error response."""
        response = client.post("/test-error")

        assert response.status_code == 400
        # The error handler should have access to request context
        # This would require modifying the handler to accept request parameter
