"""Comprehensive test utilities and fixtures."""

import array
import asyncio
import datetime
import os
import tempfile
from unittest.mock import Mock, patch

import pytest
import pytest_asyncio

from httpx import ASGITransport, AsyncClient

try:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from src.database import Base, get_async_db, models
except Exception as exc:  # pragma: no cover - defensive import guard for optional deps
    SQLALCHEMY_AVAILABLE = False
    SQLALCHEMY_IMPORT_ERROR = exc
    AsyncSession = async_sessionmaker = create_async_engine = Base = get_async_db = models = None
else:
    SQLALCHEMY_AVAILABLE = True
    SQLALCHEMY_IMPORT_ERROR = None

try:
    from src.api.main import app as _fastapi_app
except Exception as exc:  # pragma: no cover - optional FastAPI import for offline runs
    FASTAPI_AVAILABLE = False
    FASTAPI_IMPORT_ERROR = exc
    app = None
else:
    FASTAPI_AVAILABLE = True
    FASTAPI_IMPORT_ERROR = None
    app = _fastapi_app

try:
    from src.core.vector_store import VectorStore, get_vector_store
except Exception as exc:  # pragma: no cover - optional vector store fallback
    VECTOR_STORE_AVAILABLE = False
    VECTOR_STORE_IMPORT_ERROR = exc
    VectorStore = get_vector_store = None
else:
    VECTOR_STORE_AVAILABLE = True
    VECTOR_STORE_IMPORT_ERROR = None


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Provide a session-scoped event loop that cooperates with pytest-asyncio."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop_policy().new_event_loop()
        asyncio.set_event_loop(loop)
        created = True
    else:
        created = False

    try:
        yield loop
    finally:
        if created and not loop.is_closed():
            loop.close()


async def _truncate_all(session: AsyncSession) -> None:
    if not SQLALCHEMY_AVAILABLE:
        pytest.skip(f"SQLAlchemy unavailable: {SQLALCHEMY_IMPORT_ERROR}")
    for table in reversed(Base.metadata.sorted_tables):
        await session.execute(table.delete())
    await session.commit()


def _reset_vector_store() -> VectorStore:
    if not VECTOR_STORE_AVAILABLE:
        pytest.skip(f"Vector store unavailable: {VECTOR_STORE_IMPORT_ERROR}")
    VectorStore._instance = None  # type: ignore[attr-defined]
    store = VectorStore()
    store.initialize_index()
    return store


@pytest_asyncio.fixture(scope="session")
async def async_engine(tmp_path_factory: pytest.TempPathFactory):
    if not SQLALCHEMY_AVAILABLE:
        pytest.skip(f"SQLAlchemy unavailable: {SQLALCHEMY_IMPORT_ERROR}")
    db_path = tmp_path_factory.mktemp("test_dbs") / "pytest.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
def async_session_factory(async_engine):
    if not SQLALCHEMY_AVAILABLE:
        pytest.skip(f"SQLAlchemy unavailable: {SQLALCHEMY_IMPORT_ERROR}")
    return async_sessionmaker(bind=async_engine, expire_on_commit=False, autoflush=False)


@pytest_asyncio.fixture(scope="session")
async def test_db(async_session_factory):
    if not SQLALCHEMY_AVAILABLE:
        pytest.skip(f"SQLAlchemy unavailable: {SQLALCHEMY_IMPORT_ERROR}")
    if not FASTAPI_AVAILABLE:
        pytest.skip(f"FastAPI app unavailable: {FASTAPI_IMPORT_ERROR}")
    async def override_get_db():
        async with async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_async_db] = override_get_db

    async with async_session_factory() as session:
        await _truncate_all(session)

    try:
        yield async_session_factory
    finally:
        app.dependency_overrides.pop(get_async_db, None)


@pytest_asyncio.fixture
async def db_session(async_session_factory):
    if not SQLALCHEMY_AVAILABLE:
        pytest.skip(f"SQLAlchemy unavailable: {SQLALCHEMY_IMPORT_ERROR}")
    async with async_session_factory() as session:
        await _truncate_all(session)
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def populated_db(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    if not SQLALCHEMY_AVAILABLE:
        pytest.skip(f"SQLAlchemy unavailable: {SQLALCHEMY_IMPORT_ERROR}")
    await _truncate_all(db_session)

    now = datetime.datetime.now(datetime.UTC)
    report_specs = [
        {"name": "Report 1", "score": 95.0, "doc_type": "Progress Note", "discipline": "PT", "days_ago": 5},
        {"name": "Report 2", "score": 85.0, "doc_type": "Evaluation", "discipline": "PT", "days_ago": 10},
        {"name": "Report 3", "score": 75.0, "doc_type": "Progress Note", "discipline": "OT", "days_ago": 15},
        {"name": "Report 4", "score": 90.0, "doc_type": "Plan of Care", "discipline": "SLP", "days_ago": 20},
    ]

    reports = []
    for spec in report_specs:
        embedding = array.array("f", [0.0] * 16)
        embedding[:4] = array.array(
            "f",
            [
                spec["score"] / 100.0,
                spec["days_ago"] / 30.0,
                0.5,
                0.1,
            ],
        )
        report = models.AnalysisReport(
            document_name=spec["name"],
            compliance_score=spec["score"],
            document_type=spec["doc_type"],
            discipline=spec["discipline"],
            analysis_date=now - datetime.timedelta(days=spec["days_ago"]),
            analysis_result={
                "discipline": spec["discipline"],
                "document_type": spec["doc_type"],
                "summary": f"Summary for {spec['name']}",
            },
            document_embedding=embedding.tobytes(),
        )
        db_session.add(report)
        reports.append(report)

    await db_session.flush()
    ids = [report.id for report in reports]
    await db_session.commit()

    class _StubVectorStore:
        def __init__(self):
            self.is_initialized = True
            self._ids = ids

        def initialize_index(self):
            self.is_initialized = True

        def add_vectors(self, *_, **__):
            return None

        def search(self, _query_vector, k: int, threshold: float = 0.85):
            return [(rid, 0.99) for rid in self._ids if rid != 2][:k]

    stub_store = _StubVectorStore()
    monkeypatch.setattr('src.database.crud.get_vector_store', lambda: stub_store)

    try:
        yield db_session
    finally:
        await _truncate_all(db_session)


@pytest_asyncio.fixture
async def client(test_db, monkeypatch: pytest.MonkeyPatch):
    if not (SQLALCHEMY_AVAILABLE and FASTAPI_AVAILABLE and VECTOR_STORE_AVAILABLE):
        pytest.skip(
            "Skipping ASGI client: missing dependencies",
            allow_module_level=False,
        )
    async_session_factory = test_db

    async def _passthrough(self, request, call_next):
        return await call_next(request)

    monkeypatch.setattr(
        "src.api.middleware.csrf_protection.CSRFProtectionMiddleware.dispatch",
        _passthrough,
        raising=True,
    )

    async with async_session_factory() as session:
        await _truncate_all(session)

    app.user_middleware = [
        m
        for m in app.user_middleware
        if not (callable(m.cls) and getattr(m.cls, '__name__', '') == '<lambda>')
    ]
    app.middleware_stack = app.build_middleware_stack()

    transport = ASGITransport(app=app, lifespan="auto")
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


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