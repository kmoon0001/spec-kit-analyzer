import pytest
import pytest_asyncio

try:  # pragma: no cover - dependency availability
    from httpx import AsyncClient, ASGITransport
except ModuleNotFoundError as exc:  # pragma: no cover - handled via skip logic
    HTTPX_IMPORT_ERROR = exc
    AsyncClient = ASGITransport = object  # type: ignore[assignment]
else:
    HTTPX_IMPORT_ERROR = None

try:  # pragma: no cover - dependency availability
    from sqlalchemy.ext.asyncio import AsyncSession
except ModuleNotFoundError as exc:  # pragma: no cover - handled via skip logic
    SQLALCHEMY_IMPORT_ERROR = exc
    AsyncSession = object  # type: ignore[assignment]
else:
    SQLALCHEMY_IMPORT_ERROR = None

try:  # pragma: no cover - dependency availability
    from src.api.dependencies import get_analysis_service
    from src.api.main import app
    from src.auth import get_current_active_user
    from src.database import get_async_db, models
except ModuleNotFoundError as exc:  # pragma: no cover - handled via skip logic
    API_IMPORT_ERROR = exc
    get_analysis_service = get_current_active_user = get_async_db = None  # type: ignore[assignment]
    app = None  # type: ignore[assignment]
    models = None  # type: ignore[assignment]
else:
    API_IMPORT_ERROR = None


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    if SQLALCHEMY_IMPORT_ERROR is not None:
        pytest.skip(
            "SQLAlchemy is required for API database fixtures but is not installed in this environment.",
            allow_module_level=True,
        )
    if HTTPX_IMPORT_ERROR is not None:
        pytest.skip(
            "httpx is required for API client fixtures but is not installed in this environment.",
            allow_module_level=True,
        )
    if API_IMPORT_ERROR is not None:
        pytest.skip(
            "FastAPI dependencies are unavailable; API tests cannot run in this environment.",
            allow_module_level=True,
        )

    async def override_get_async_db() -> AsyncSession:
        yield db_session

    app.dependency_overrides[get_async_db] = override_get_async_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
