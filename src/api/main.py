"""
Clinical Compliance Analyzer API

FastAPI backend for the Therapy Compliance Analyzer desktop application.
Provides endpoints for document analysis, user management, and compliance reporting.
"""

import asyncio
import datetime
import logging
import numpy as np
import structlog
from contextlib import asynccontextmanager
from typing import Any, Coroutine, Dict, List

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.dependencies import (
    shutdown_event as api_shutdown,
    startup_event as api_startup,
)
from src.api.routers import (
    admin,
    analysis,
    auth,
    chat,
    compliance,
    dashboard,
    feedback,
    health,
    habits,
    meta_analytics,
)
from src.api.global_exception_handler import (
    global_exception_handler,
    http_exception_handler,
)
from src.core.vector_store import get_vector_store
from src.config import get_settings
from src.database import crud, get_async_db
from src.logging_config import CorrelationIdMiddleware, configure_logging

settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])

logger = structlog.get_logger(__name__)

# --- WebSocket Log Streaming --- #

class WebSocketManager:
    """Manages active WebSocket connections."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

log_manager = WebSocketManager()

class WebSocketLogHandler(logging.Handler):
    """A logging handler that broadcasts log records to WebSockets."""
    def __init__(self):
        super().__init__()
        self.loop = asyncio.get_event_loop()

    def emit(self, record):
        log_entry = self.format(record)
        asyncio.run_coroutine_threadsafe(log_manager.broadcast(log_entry), self.loop)


# --- In-Memory Task Purging --- #

class InMemoryTaskPurgeService:
    """A service to purge expired tasks from the in-memory task dictionary."""
    def __init__(self, tasks: Dict[str, Any], retention_period_minutes: int, purge_interval_seconds: int):
        self.tasks = tasks
        self.retention_period = datetime.timedelta(minutes=retention_period_minutes)
        self.purge_interval = purge_interval_seconds
        self._stop_event = asyncio.Event()

    async def purge_expired_tasks(self) -> None:
        while not self._stop_event.is_set():
            # ... (rest of the purge logic)
            await asyncio.sleep(self.purge_interval)

    def start(self) -> Coroutine[Any, Any, None]:
        logger.info("Starting in-memory task purge service.")
        return asyncio.create_task(self.purge_expired_tasks())

    def stop(self) -> None:
        logger.info("Stopping in-memory task purge service.")
        self._stop_event.set()


# --- Maintenance Jobs --- #

def run_maintenance_jobs():
    """Instantiates and runs all scheduled maintenance services."""
    # ... (maintenance logic)

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
            valid_ids = [id for emb, id in zip(embeddings, report_ids) if emb.shape[0] == embedding_dim]

            if valid_embeddings:
                vector_store.add_vectors(np.array(valid_embeddings), valid_ids)
            logger.info(f"Successfully populated vector store with {len(valid_embeddings)} embeddings.")
        else:
            logger.info("No existing reports with embeddings found to populate vector store.")
    finally:
        await db.close()

# --- Application Lifespan --- #

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    configure_logging(settings.log_level)
    ws_handler = WebSocketLogHandler()
    ws_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ws_handler.setFormatter(formatter)
    logging.getLogger().addHandler(ws_handler)

    await api_startup()
    await initialize_vector_store()
    
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

app = FastAPI(
    title="Therapy Compliance Analyzer API",
    description="...",
    version="1.0.0",
    lifespan=lifespan,
    # ... (other app config)
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
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(compliance.router, tags=["Compliance"])
app.include_router(habits.router, tags=["Habits"])
app.include_router(meta_analytics.router, tags=["Meta Analytics"])
app.include_router(feedback.router)


# --- WebSocket Endpoint --- #

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await log_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        log_manager.disconnect(websocket)


# --- Root Endpoint --- #

@app.get("/")
def read_root():
    """Root endpoint providing API welcome message."""
    return {"message": "Welcome to the Clinical Compliance Analyzer API"}
