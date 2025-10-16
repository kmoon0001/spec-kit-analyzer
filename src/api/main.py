"""Clinical Compliance Analyzer API

FastAPI backend for the Therapy Compliance Analyzer desktop application.
Provides endpoints for document analysis, user management, and compliance reporting.
"""

import asyncio
import json
import logging
import sys
import time
from collections.abc import Coroutine
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Any

import numpy as np
import structlog
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from sqlalchemy import select

from src.api.dependencies import shutdown_event as api_shutdown
from src.api.dependencies import startup_event as api_startup
from src.auth import get_auth_service
from src.api.routers import (
    admin,
    analysis,
    auth,
    chat,
    compliance,
    dashboard,
    feedback,
    habits,
    health,
    meta_analytics,
    preferences,
    users,
    rubric_router,
    individual_habits,
    websocket as websocket_routes,
)

try:
    from src.api.routers import ehr_integration

    EHR_AVAILABLE = True
except ImportError:
    EHR_AVAILABLE = False

from src.api.global_exception_handler import global_exception_handler, http_exception_handler
from src.config import get_settings
from src.core.vector_store import get_vector_store
from src.database import crud, get_async_db, models
from src.database import init_db
from src.database.database import AsyncSessionLocal
from src.logging_config import CorrelationIdMiddleware, configure_logging

settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])

logger = structlog.get_logger(__name__)

# --- WebSocket Log Streaming --- #


class WebSocketLogHandler(logging.Handler):
    """A logging handler that broadcasts log records to connected WebSocket clients."""

    def __init__(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        super().__init__()
        try:
            self.loop = loop or asyncio.get_running_loop()
        except RuntimeError:
            self.loop = None

    def emit(self, record: logging.LogRecord) -> None:
        if not self.loop or self.loop.is_closed():
            return

        payload = {
            "type": "log",
            "level": record.levelname,
            "logger": record.name,
            "message": self.format(record),
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            asyncio.run_coroutine_threadsafe(
                websocket_routes.manager.send_message("log_stream", payload),
                self.loop,
            )
        except RuntimeError:
            logger.debug("WebSocket loop unavailable; skipping log broadcast")


# --- In-Memory Task Purging --- #


class InMemoryTaskPurgeService:
    """A service to purge expired tasks from the in-memory task dictionary."""

    def __init__(self, tasks=None, retention_period_minutes=60, purge_interval_seconds=300):
        self.tasks = tasks or {}
        self.retention_period_minutes = retention_period_minutes
        self.purge_interval_seconds = purge_interval_seconds
        self._stop_event = asyncio.Event()

    def start(self) -> Coroutine[Any, Any, None]:
        logger.info("Starting in-memory task purge service.")
        return asyncio.create_task(self.purge_expired_tasks())

    def stop(self) -> None:
        logger.info("Stopping in-memory task purge service.")
        self._stop_event.set()

    async def purge_expired_tasks(self):
        """Purge expired tasks from memory."""
        while not self._stop_event.is_set():
            try:
                current_time = time.time()
                expired_keys = [
                    key
                    for key, task in self.tasks.items()
                    if current_time - task.get("created_at", 0) > (self.retention_period_minutes * 60)
                ]
                for key in expired_keys:
                    self.tasks.pop(key, None)

                await asyncio.sleep(self.purge_interval_seconds)
            except Exception as e:
                logger.error(f"Error in task purge: {e}")
                await asyncio.sleep(60)


# --- Maintenance Jobs --- #


def run_maintenance_jobs():
    """Instantiates and runs all scheduled maintenance services."""
    # Placeholder for future maintenance tasks


scheduler = BackgroundScheduler(daemon=True)
in_memory_task_purge_service = InMemoryTaskPurgeService(
    tasks=analysis.tasks,
    retention_period_minutes=settings.maintenance.in_memory_retention_minutes,
    purge_interval_seconds=settings.maintenance.in_memory_purge_interval_seconds,
)

# --- Vector Store Initialization ---


async def initialize_vector_store():
    """Initializes and populates the vector store on application startup."""
    vector_store = get_vector_store()
    if vector_store.is_initialized:
        return

    vector_store.initialize_index()
    logger.info("Populating vector store with existing report embeddings...")

    db_session_gen = get_async_db()
    db = await db_session_gen.__anext__()
    try:
        reports = await crud.get_all_reports_with_embeddings(db)
        if reports:
            embeddings = [np.frombuffer(report.document_embedding, dtype=np.float32) for report in reports]
            report_ids = [report.id for report in reports]

            # Ensure all embeddings have the same dimension
            embedding_dim = embeddings[0].shape[0]
            valid_embeddings = [emb for emb in embeddings if emb.shape[0] == embedding_dim]
            valid_ids = [id for emb, id in zip(embeddings, report_ids, strict=False) if emb.shape[0] == embedding_dim]

            if valid_embeddings:
                vector_store.add_vectors(np.array(valid_embeddings), valid_ids)
            logger.info("Successfully populated vector store with %s embeddings.", len(valid_embeddings))
        else:
            logger.info("No existing reports with embeddings found to populate vector store.")
    finally:
        await db.close()


async def auto_warm_ai_models():
    """Auto-warm AI models with tiny prompts to reduce first-use latency."""
    logger.info("Starting AI model auto-warming...")

    try:
        # Import AI services
        from src.core.analysis_service import AnalysisService
        from src.core.hybrid_retriever import HybridRetriever

        # Initialize retriever
        retriever = HybridRetriever()
        await retriever.initialize()

        # Initialize analysis service
        analysis_service = AnalysisService(retriever=retriever)

        # Skip auto-warming if using mocks
        if analysis_service.use_mocks:
            logger.info("Skipping AI model auto-warming (mocks enabled)")
            return

        # Tiny warm-up prompts
        warm_prompts = ["Test", "Hello", "Sample note", "Patient visit", "Assessment"]

        # Staggered warming with delays
        for i, prompt in enumerate(warm_prompts):
            try:
                logger.info(f"Auto-warming AI models with prompt {i + 1}/{len(warm_prompts)}: '{prompt}'")

                # Warm up document classifier (if available)
                if analysis_service.document_classifier is not None:
                    analysis_service.document_classifier.classify_document(prompt)

                # Warm up NER (skip for now - heavy on CPU)

                # Small delay between warm-ups
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.warning(f"Auto-warm failed for prompt '{prompt}': {e}")
                continue

        logger.info("AI model auto-warming completed successfully")

    except Exception as e:
        logger.warning(f"Auto-warm initialization failed: {e}")
        # Don't fail startup if auto-warm fails


# --- Application Lifespan --- #


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    configure_logging(settings.log_level)
    if "pytest" not in sys.modules:
        ws_handler = WebSocketLogHandler()
        ws_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ws_handler.setFormatter(formatter)
        logging.getLogger().addHandler(ws_handler)

    # Ensure database schema is initialized before using any DB-dependent services
    await init_db()

    await api_startup()
    await initialize_vector_store()

    # Auto-warm AI models in background to reduce first-use latency
    # Note: This runs as a background task and should not block startup
    asyncio.create_task(auto_warm_ai_models())

    run_maintenance_jobs()
    scheduler.add_job(run_maintenance_jobs, "interval", days=1)
    scheduler.start()
    logger.info("Scheduler started for daily maintenance tasks.")

    in_memory_task_purge_service.start()

    yield

    await api_shutdown()
    scheduler.shutdown()
    in_memory_task_purge_service.stop()


# --- FastAPI App Initialization --- #

ALLOWED_CORS_ORIGINS = [
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://localhost",
    "http://localhost:3000",
    "https://127.0.0.1",
    "https://127.0.0.1:3000",
    "https://localhost",
    "https://localhost:3000",
    # Electron specific origins
    "app://.",
    "file://",
]

# Enhanced CORS regex for Electron, Capacitor, and other desktop frameworks
ALLOWED_CORS_REGEX = r"^(app|file|capacitor|electron)://.*$"

app = FastAPI(
    title="Therapy Compliance Analyzer API",
    description="...",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: allow localhost only (development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_CORS_ORIGINS,
    allow_origin_regex=ALLOWED_CORS_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(CorrelationIdMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# --- Routers --- #

app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(analysis.router, tags=["Analysis"])
app.include_router(analysis.legacy_router, tags=["Analysis Legacy"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(compliance.router, tags=["Compliance"])
app.include_router(habits.router, tags=["Habits"])
app.include_router(meta_analytics.router, tags=["Meta Analytics"])
app.include_router(feedback.router)
app.include_router(users.router, tags=["Users"])
app.include_router(preferences.router)
app.include_router(rubric_router.router, prefix="/rubrics", tags=["Rubrics"])
app.include_router(individual_habits.router)
app.include_router(websocket_routes.router, tags=["WebSocket"])

if EHR_AVAILABLE:
    app.include_router(ehr_integration.router, tags=["EHR Integration"])
    logging.info("EHR Integration API enabled")

# Include plugin management
try:
    from src.api.routers import plugins
    from src.core.plugin_system import PluginManager

    plugin_manager = PluginManager()
    app.include_router(plugins.router, tags=["Plugin Management"])
    logging.info("Plugin Management API enabled")
except ImportError:
    plugin_manager = None
    logging.warning("Plugin Management API not available")

# --- WebSocket Endpoint --- #

async def _load_all_plugins_background():
    """Background task to load all plugins."""
    results = {}  # Initialize results to an empty dictionary
    try:
        if plugin_manager is None:
            logger.info("Plugin manager not available, skipping plugin loading")
            return
            
        logger.info("Starting background plugin loading")
        results = plugin_manager.load_all_plugins()
        logger.info(f"Background plugin loading completed with results: {results}")
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.exception("Background plugin loading failed due to data error: %s", e)
    except Exception as e:
        logger.error(f"Error during background plugin loading: {e}")

    successful_loads = sum(1 for success in results.values() if success)
    total_plugins = len(results)
    logger.info("Background plugin loading complete: %s/%s successful", successful_loads, total_plugins)
@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return

    auth_service = get_auth_service()
    try:
        payload = jwt.decode(token, auth_service.secret_key, algorithms=[auth_service.algorithm])
    except JWTError:
        await websocket.close(code=1008, reason="Invalid token")
        return

    username = payload.get("sub")
    if not username:
        await websocket.close(code=1008, reason="Invalid token payload")
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(models.User).where(models.User.username == username))
        user = result.scalars().first()
        if not user or not user.is_active:
            await websocket.close(code=1008, reason="Unauthorized")
            return

    await websocket_routes.manager.connect(websocket, "log_stream")
    await websocket.send_json(
        {
            "type": "connected",
            "message": "Log stream connected",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("Log stream client disconnected", username=username)
    except Exception as exc:
        logger.exception("Log stream error", error=str(exc))
    finally:
        websocket_routes.manager.disconnect(websocket, "log_stream")


# Minimal logs stream endpoint for compatibility with GUI pollers
@app.get("/logs/stream")
async def logs_stream():
    return {"status": "ok", "message": "log stream endpoint available"}


# --- Root Endpoint --- #


@app.get("/")
def read_root():
    """Root endpoint providing API welcome message."""
    return {"message": "Welcome to the Clinical Compliance Analyzer API"}