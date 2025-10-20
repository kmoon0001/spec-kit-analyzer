"""Clinical Compliance Analyzer API

FastAPI backend for the Therapy Compliance Analyzer desktop application.
Provides endpoints for document analysis, user management, and compliance reporting.
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from contextlib import asynccontextmanager

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
    advanced_analytics,
    analysis,
    auth,
    chat,
    cleanup,
    compliance,
    dashboard,
    feedback,
    habits,
    health,
    meta_analytics,
    performance,
    preferences,
    sessions,
    users,
    rubric_router,
    individual_habits,
    websocket as websocket_routes,
    strictness,
)

try:
    from src.api.routers import ehr_integration

    EHR_AVAILABLE = True
except ImportError:
    EHR_AVAILABLE = False

from src.api.global_exception_handler import global_exception_handler, http_exception_handler
from src.api.middleware.request_tracking import RequestIdMiddleware, get_request_tracker
from src.api.middleware.csrf_protection import CSRFProtectionMiddleware
from src.api.middleware.enhanced_rate_limiting import EnhancedRateLimitMiddleware
from src.api.middleware.performance_monitoring import PerformanceMonitoringMiddleware
from src.core.enhanced_logging import initialize_logging
from src.api.error_handling import get_error_handler
from src.config import get_settings
from src.core.vector_store import get_vector_store
from src.core.file_cleanup_service import start_cleanup_service, stop_cleanup_service
from src.core.document_cleanup_service import start_cleanup_service as start_doc_cleanup, stop_cleanup_service as stop_doc_cleanup
from src.core.cleanup_services import start_cleanup_services, stop_cleanup_services
from src.database import crud, get_async_db, models
from src.database import init_db
from src.database.database import AsyncSessionLocal
from src.logging_config import CorrelationIdMiddleware, configure_logging
from src.core.service_manager import service_manager, create_default_services
from src.core.persistent_task_registry import persistent_task_registry
from src.core.enhanced_worker_manager import enhanced_worker_manager

settings = get_settings()

# Import enhanced features (with error handling for tests)
try:
    from src.api.middleware.input_validation import InputValidationMiddleware
    from src.api.middleware.request_logging import RequestLoggingMiddleware
    from src.api.graceful_shutdown import lifespan_with_graceful_shutdown, register_background_task
    from src.api.enhanced_error_context import enhanced_exception_handler
    from src.api.documentation import create_custom_openapi, add_api_documentation_routes
    from src.core.performance_metrics_collector import metrics_collector, update_system_metrics_task
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    logger = structlog.get_logger(__name__)
    logger.warning(f"Enhanced features not available: {e}")
    ENHANCED_FEATURES_AVAILABLE = False
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
            self.loop = None  # type: ignore[assignment]

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

    def start(self) -> asyncio.Task[None]:
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
            valid_ids = [id for emb, id in zip(embeddings, report_ids, strict=True) if emb.shape[0] == embedding_dim]

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

        # Store in app state for dependency injection
        from src.api.dependencies import app_state
        app_state["analysis_service"] = analysis_service

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
    """Enhanced lifespan context manager with graceful shutdown and metrics."""
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

    # Start background metrics collection (if available)
    if ENHANCED_FEATURES_AVAILABLE:
        metrics_task = asyncio.create_task(update_system_metrics_task())
        register_background_task(metrics_task)

    run_maintenance_jobs()
    scheduler.add_job(run_maintenance_jobs, "interval", days=1)
    scheduler.start()
    logger.info("Scheduler started for daily maintenance tasks.")

    # Start the task purge service
    _ = in_memory_task_purge_service.start()

    # Start file cleanup service
    await start_cleanup_service()

    # Start document cleanup service
    await start_doc_cleanup()

    # Start comprehensive cleanup services
    await start_cleanup_services()

    # Initialize request tracker
    request_tracker = get_request_tracker()
    logger.info("Request tracking initialized")

    # Initialize error handler
    error_handler = get_error_handler()
    logger.info("Error handling initialized")

    # Initialize enhanced services
    await enhanced_worker_manager.start()
    logger.info("Enhanced worker manager started")

    # Initialize persistent task registry
    await persistent_task_registry.cleanup_old_tasks(days_old=7)
    logger.info("Persistent task registry initialized")

    # Initialize service manager
    default_services = create_default_services()
    logger.info("Service manager initialized")

    yield

    await api_shutdown()
    scheduler.shutdown()
    in_memory_task_purge_service.stop()
    stop_cleanup_service()
    await stop_doc_cleanup()
    await stop_cleanup_services()

    # Shutdown enhanced services
    await enhanced_worker_manager.stop()
    logger.info("Enhanced worker manager stopped")

    await persistent_task_registry.close()
    logger.info("Persistent task registry closed")


# --- FastAPI App Initialization --- #

ALLOWED_CORS_ORIGINS = [
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "https://127.0.0.1",
    "https://127.0.0.1:3000",
    "https://127.0.0.1:3001",
    "https://localhost",
    "https://localhost:3000",
    "https://localhost:3001",
    # Electron specific origins
    "app://.",
    "file://",
]

# Enhanced CORS regex for Electron, Capacitor, and other desktop frameworks
ALLOWED_CORS_REGEX = r"^(app|file|capacitor|electron)://.*$"

app = FastAPI(
    title="Therapy Compliance Analyzer API",
    description="AI-powered clinical documentation compliance analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# Set custom OpenAPI schema (if available)
if ENHANCED_FEATURES_AVAILABLE:
    app.openapi = lambda: create_custom_openapi(app)

# CORS: allow localhost only (development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_CORS_ORIGINS,
    allow_origin_regex=ALLOWED_CORS_REGEX,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
)

# Add enhanced middleware stack (if available)
if ENHANCED_FEATURES_AVAILABLE:
    app.add_middleware(InputValidationMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
else:
    logger.warning("Enhanced middleware not available, using basic setup")

# Initialize enhanced logging
initialize_logging()

# Add performance monitoring middleware
app.add_middleware(PerformanceMonitoringMiddleware)

# Add enhanced rate limiting middleware
app.add_middleware(EnhancedRateLimitMiddleware)

# Add CSRF protection middleware
app.add_middleware(lambda app: CSRFProtectionMiddleware(
    app,
    settings.auth.secret_key.get_secret_value()
))

app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(RequestIdMiddleware)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)

    # Essential security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=(), payment=(), usb=()"

    # Content Security Policy
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Allow inline scripts for Electron
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "font-src 'self' data:; "
        "connect-src 'self' ws: wss:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    response.headers["Content-Security-Policy"] = csp_policy

    # Strict Transport Security (HTTPS only)
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

    # Additional security headers
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

    return response
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, global_exception_handler)

# --- Routers --- #

app.include_router(health.router, tags=["Health"])
app.include_router(cleanup.router, tags=["Cleanup"])
app.include_router(performance.router, tags=["Performance"])

# Include enhanced health check router (if available)
if ENHANCED_FEATURES_AVAILABLE:
    try:
        from src.api.routers import health_advanced
        app.include_router(health_advanced.router, tags=["Health"])
    except ImportError:
        logger.warning("Enhanced health check router not available")
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(sessions.router, tags=["Sessions"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(analysis.router, tags=["Analysis"])
app.include_router(analysis.legacy_router, tags=["Analysis Legacy"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(compliance.router, tags=["Compliance"])
app.include_router(habits.router, tags=["Habits"])
app.include_router(advanced_analytics.router, tags=["Advanced Analytics"])
app.include_router(meta_analytics.router, tags=["Meta Analytics"])
app.include_router(feedback.router)
app.include_router(users.router, tags=["Users"])
app.include_router(preferences.router)
app.include_router(rubric_router.router, prefix="/rubrics", tags=["Rubrics"])
app.include_router(individual_habits.router)
app.include_router(websocket_routes.router, tags=["WebSocket"])
app.include_router(strictness.router, tags=["Strictness"])

if EHR_AVAILABLE:
    app.include_router(ehr_integration.router, tags=["EHR Integration"])
    logging.info("EHR Integration API enabled")

# Add documentation routes (if available)
if ENHANCED_FEATURES_AVAILABLE:
    add_api_documentation_routes(app)

# Add metrics endpoint (if available)
if ENHANCED_FEATURES_AVAILABLE:
    @app.get("/metrics", tags=["Monitoring"])
    async def get_metrics():
        """Get application performance metrics."""
        return metrics_collector.get_metrics_summary()

# Include plugin management
try:
    from src.api.routers import plugins
    from src.core.plugin_system import PluginManager

    plugin_manager = PluginManager()
    app.include_router(plugins.router, tags=["Plugin Management"])
    logging.info("Plugin Management API enabled")
except ImportError:
    plugin_manager = None  # type: ignore[assignment]
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
