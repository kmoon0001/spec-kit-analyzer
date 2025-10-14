import os
import sys
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import patch

import pytest
import pytest_asyncio

pytest_plugins = ("pytest_asyncio",)

try:  # pragma: no cover - dependency availability
    import numpy as np
except ModuleNotFoundError as exc:  # pragma: no cover - handled via skip logic
    NUMPY_IMPORT_ERROR = exc
    np = None  # type: ignore[assignment]
else:
    NUMPY_IMPORT_ERROR = None

try:  # pragma: no cover - dependency availability
    from sqlalchemy import delete
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
except ModuleNotFoundError as exc:  # pragma: no cover - handled via skip logic
    SQLALCHEMY_IMPORT_ERROR = exc
    delete = None  # type: ignore[assignment]
    AsyncSession = Any  # type: ignore[assignment]
    create_async_engine = None  # type: ignore[assignment]
    sessionmaker = None  # type: ignore[assignment]
else:
    SQLALCHEMY_IMPORT_ERROR = None

from src.core.vector_store import get_vector_store

if SQLALCHEMY_IMPORT_ERROR is None:
    from src.database import Base, models
else:  # pragma: no cover - dependency missing
    Base = None  # type: ignore[assignment]
    models = None  # type: ignore[assignment]

try:  # pragma: no cover - environment dependent
    import PySide6  # type: ignore[import-not-found]
    from PySide6.QtWidgets import QApplication
except Exception as exc:  # pragma: no cover - handled via skip logic
    PySide6 = None  # type: ignore[assignment]
    QApplication = None  # type: ignore[assignment]
    _QT_IMPORT_ERROR: Exception | None = exc
    _QT_IS_STUB = False
else:  # pragma: no cover - environment dependent
    _QT_IMPORT_ERROR = None
    _QT_IS_STUB = bool(getattr(PySide6, "__FAKE_PYSIDE6__", False))

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

if SQLALCHEMY_IMPORT_ERROR is None:
    engine = create_async_engine(TEST_DATABASE_URL)
    TestingSessionLocal = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
else:  # pragma: no cover - dependency missing
    engine = None  # type: ignore[assignment]
    TestingSessionLocal = None  # type: ignore[assignment]


if SQLALCHEMY_IMPORT_ERROR is None:

    @pytest_asyncio.fixture(scope="session", autouse=True)
    async def setup_database():
        """Creates the test database and tables for the test session."""
        if os.path.exists("test.db"):
            try:
                os.remove("test.db")
            except PermissionError:
                await engine.dispose()
                try:
                    os.remove("test.db")
                except PermissionError as e:
                    pytest.fail(f"Could not remove test.db, it is locked: {e}")

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield
        await engine.dispose()
        if os.path.exists("test.db"):
            try:
                os.remove("test.db")
            except PermissionError:
                pass

    @pytest_asyncio.fixture
    async def db_session() -> AsyncSession:
        """Provides a clean database session for each test."""
        async with TestingSessionLocal() as session:
            yield session

    @pytest_asyncio.fixture
    async def populated_db(db_session: AsyncSession) -> AsyncSession:
        """Clears and populates the database with a set of test data."""
        if NUMPY_IMPORT_ERROR is not None:
            pytest.skip(
                "NumPy is required for database vector fixtures but is not installed in this environment.",
                allow_module_level=True,
            )
        await db_session.execute(delete(models.AnalysisReport))
        await db_session.commit()

        reports_data = [
            models.AnalysisReport(
                id=1,
                document_name="report_1.txt",
                compliance_score=95.0,
                document_type="Progress Note",
                analysis_date=datetime.now(UTC) - timedelta(days=5),
                analysis_result={"discipline": "PT"},
                document_embedding=np.random.rand(768).astype(np.float32).tobytes(),
            ),
            models.AnalysisReport(
                id=2,
                document_name="report_2.txt",
                compliance_score=85.0,
                document_type="Evaluation",
                analysis_date=datetime.now(UTC) - timedelta(days=10),
                analysis_result={"discipline": "PT"},
                document_embedding=np.random.rand(768).astype(np.float32).tobytes(),
            ),
            models.AnalysisReport(
                id=3,
                document_name="report_3.txt",
                compliance_score=75.0,
                document_type="Progress Note",
                analysis_date=datetime.now(UTC) - timedelta(days=15),
                analysis_result={"discipline": "OT"},
                document_embedding=np.random.rand(768).astype(np.float32).tobytes(),
            ),
            models.AnalysisReport(
                id=4,
                document_name="report_4.txt",
                compliance_score=90.0,
                document_type="Discharge Summary",
                analysis_date=datetime.now(UTC) - timedelta(days=20),
                analysis_result={"discipline": "SLP"},
                document_embedding=np.random.rand(768).astype(np.float32).tobytes(),
            ),
        ]
        db_session.add_all(reports_data)
        await db_session.commit()

        vector_store = get_vector_store()
        if not vector_store.is_initialized:
            vector_store.initialize_index()

        embeddings = np.array(
            [np.frombuffer(r.document_embedding, dtype=np.float32) for r in reports_data if r.document_embedding]
        )
        ids = [r.id for r in reports_data if r.document_embedding]
        if len(embeddings) > 0:
            vector_store.add_vectors(embeddings, ids)

        return db_session

else:  # pragma: no cover - dependency missing

    @pytest_asyncio.fixture(scope="session")
    async def setup_database():
        pytest.skip(
            "SQLAlchemy is required for database-dependent tests but is not installed in this environment.",
            allow_module_level=True,
        )

    @pytest_asyncio.fixture
    async def db_session():
        pytest.skip(
            "SQLAlchemy is required for the db_session fixture but is not installed in this environment.",
            allow_module_level=True,
        )

    @pytest_asyncio.fixture
    async def populated_db():
        pytest.skip(
            "SQLAlchemy is required for the populated_db fixture but is not installed in this environment.",
            allow_module_level=True,
        )


def _ensure_qapplication() -> QApplication:
    if (
        QApplication is None
        or _QT_IMPORT_ERROR is not None
        or _QT_IS_STUB
    ):  # pragma: no cover - skip handled elsewhere
        raise RuntimeError("Qt application cannot be created without GUI dependencies.")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def qapp() -> Iterator[QApplication]:
    """Provide a QApplication instance or skip if Qt cannot initialize."""

    if _QT_IMPORT_ERROR is not None:
        pytest.skip(f"Qt GUI dependencies unavailable: {_QT_IMPORT_ERROR}")
    if _QT_IS_STUB:
        pytest.skip("Qt GUI dependencies replaced with stub implementation.")

    app = _ensure_qapplication()
    yield app


@pytest.fixture
def qtbot(qapp, request):
    """Fallback qtbot fixture that defers to pytest-qt when available."""

    if _QT_IMPORT_ERROR is not None:
        pytest.skip(f"Qt GUI dependencies unavailable: {_QT_IMPORT_ERROR}")
    if _QT_IS_STUB:
        pytest.skip("Qt GUI dependencies replaced with stub implementation.")

    from pytestqt.qtbot import QtBot  # Lazy import to avoid ImportError during collection

    _ = qapp  # ensure QApplication fixture is initialized
    bot = QtBot(request)
    yield bot


@pytest.fixture(autouse=True)
def mock_global_services():
    """Globally mock backend services to avoid real network calls during tests."""

    with patch("requests.post") as mock_post:
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {"access_token": "fake-token"}
        yield


def pytest_ignore_collect(path, config):  # pragma: no cover - collection control
    del config  # config unused by this helper
    path_str = str(path)
    if SQLALCHEMY_IMPORT_ERROR is not None:
        if any(segment in path_str for segment in ("tests/api", "tests/integration")):
            return True
    if NUMPY_IMPORT_ERROR is not None:
        if "tests/unit" in path_str:
            return True
    if _QT_IS_STUB:
        if any(segment in path_str for segment in ("tests/gui", "tests/_stability", "tests/integration")):
            return True
    return False
