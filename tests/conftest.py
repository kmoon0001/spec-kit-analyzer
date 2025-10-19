"""Comprehensive test utilities and fixtures."""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.api.main import app
from src.database import Base, get_async_db


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_db():
    """Create test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_async_db] = override_get_db
    yield TestingSessionLocal
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def authenticated_client(client):
    """Create authenticated test client."""
    # Mock authentication
    with patch('src.auth.get_auth_service') as mock_auth:
        mock_auth.return_value.verify_password.return_value = True
        mock_auth.return_value.create_access_token.return_value = "test-token"

        # Login to get token
        response = client.post("/auth/login", json={
            "username": "test",
            "password": "test"
        })

        if response.status_code == 200:
            token = response.json().get("access_token", "test-token")
            client.headers.update({"Authorization": f"Bearer {token}"})

        yield client


@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing."""
    with patch('src.core.analysis_service.AnalysisService') as mock_service:
        mock_instance = Mock()
        mock_instance.use_mocks = True
        mock_instance.analyze_document.return_value = {
            "compliance_score": 85.5,
            "findings": [
                {
                    "rule_id": "test_rule",
                    "risk": "Medium",
                    "message": "Test finding",
                    "confidence": 0.8
                }
            ]
        }
        mock_service.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_document():
    """Create sample document for testing."""
    content = """
    Patient Progress Note

    Patient: John Doe
    Date: 2024-01-01

    Assessment:
    Patient presents with improved mobility and strength.
    Treatment goals are being met.

    Plan:
    Continue current treatment plan.
    Reassess in 2 weeks.
    """

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    try:
        os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def sample_pdf():
    """Create sample PDF for testing."""
    # This would create a minimal PDF file
    # For now, we'll use a text file with PDF extension
    content = b"PDF content placeholder"

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    try:
        os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def mock_file_upload():
    """Mock file upload for testing."""
    return {
        "file": ("test.txt", "test content", "text/plain"),
        "document_name": "Test Document",
        "rubric": "pt_compliance_rubric"
    }


@pytest.fixture
def performance_test_data():
    """Create performance test data."""
    return {
        "requests": [
            {"method": "GET", "url": "/health/", "expected_time": 0.1},
            {"method": "POST", "url": "/analysis/start", "expected_time": 0.5},
            {"method": "GET", "url": "/metrics", "expected_time": 0.2}
        ],
        "concurrent_users": 10,
        "duration_seconds": 30
    }


@pytest.fixture
def security_test_payloads():
    """Security test payloads."""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ],
        "xss": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts"
        ],
        "command_injection": [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& whoami"
        ]
    }


@pytest.fixture
def mock_metrics_collector():
    """Mock metrics collector for testing."""
    with patch('src.core.performance_metrics_collector.metrics_collector') as mock_collector:
        mock_collector.get_metrics_summary.return_value = {
            "uptime_seconds": 3600,
            "requests": {
                "total": 100,
                "avg_duration_ms": 150.5,
                "error_count": 5,
                "error_rate_percent": 5.0
            },
            "system": {
                "memory_usage_mb": 512.0,
                "cpu_usage_percent": 25.5
            }
        }
        yield mock_collector


@pytest.fixture
def mock_health_checker():
    """Mock health checker for testing."""
    with patch('src.api.routers.health_advanced.health_checker') as mock_checker:
        mock_checker.get_overall_health.return_value = {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "uptime_seconds": 3600,
            "checks": {
                "database": {"status": "healthy"},
                "ai_models": {"status": "healthy"},
                "system_resources": {"status": "healthy"}
            }
        }
        yield mock_checker


@pytest.fixture
def test_config():
    """Test configuration."""
    return {
        "use_ai_mocks": True,
        "database_url": "sqlite:///:memory:",
        "log_level": "DEBUG",
        "max_request_size": 1024,
        "rate_limit": "100/minute"
    }


@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        "SECRET_KEY": "test-secret-key",
        "ENVIRONMENT": "testing",
        "USE_AI_MOCKS": "true",
        "LOG_LEVEL": "DEBUG"
    }):
        yield


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection for testing."""
    mock_ws = Mock()
    mock_ws.accept = Mock()
    mock_ws.send_json = Mock()
    mock_ws.receive_text = Mock()
    mock_ws.close = Mock()
    return mock_ws


@pytest.fixture
def mock_task_manager():
    """Mock task manager for testing."""
    with patch('src.api.routers.analysis.tasks', {}) as mock_tasks:
        yield mock_tasks


@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing."""
    with patch('src.core.vector_store.get_vector_store') as mock_store:
        mock_instance = Mock()
        mock_instance.is_initialized = True
        mock_instance.add_vectors = Mock()
        mock_store.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing."""
    with patch('src.core.llm_service.LLMService') as mock_service:
        mock_instance = Mock()
        mock_instance.is_ready.return_value = True
        mock_instance.generate.return_value = "Mock response"
        mock_service.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_retriever():
    """Mock retriever for testing."""
    with patch('src.core.hybrid_retriever.HybridRetriever') as mock_retriever:
        mock_instance = Mock()
        mock_instance.initialize = Mock()
        mock_instance.retrieve.return_value = [
            {"text": "Mock retrieved text", "score": 0.9}
        ]
        mock_retriever.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_ner_service():
    """Mock NER service for testing."""
    with patch('src.core.ner.ClinicalNERService') as mock_service:
        mock_instance = Mock()
        mock_instance.extract_entities.return_value = [
            {"text": "Patient", "label": "PERSON", "confidence": 0.9}
        ]
        mock_service.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "username": "testuser",
        "password": "testpassword",
        "is_active": True,
        "is_admin": False
    }


@pytest.fixture
def test_analysis_data():
    """Test analysis data."""
    return {
        "document_name": "Test Document",
        "rubric": "pt_compliance_rubric",
        "strictness": "standard",
        "discipline": "pt"
    }


@pytest.fixture
def test_report_data():
    """Test report data."""
    return {
        "id": 1,
        "document_name": "Test Document",
        "compliance_score": 85.5,
        "analysis_date": "2024-01-01T00:00:00Z",
        "findings": [
            {
                "rule_id": "test_rule",
                "risk": "Medium",
                "message": "Test finding",
                "confidence": 0.8
            }
        ]
    }


# Test markers
pytestmark = [
    pytest.mark.asyncio,
]