"""Database configuration and session management.

Provides async database engine, session factory, and utility functions
for database initialization and connection management with performance optimization.
"""

import logging
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool

from ..config import get_settings

logger = logging.getLogger(__name__)

# --- Database Configuration ---
settings = get_settings()
DATABASE_URL = settings.database.url

# Ensure the URL is async-compatible for SQLite
if "sqlite" in DATABASE_URL and "aiosqlite" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")


# --- Performance Configuration ---
def _get_performance_config() -> Any | None:
    """Safely get performance configuration with fallback."""
    # Temporarily disabled for faster startup
    logger.debug("Performance manager disabled for faster startup")
    return None


# Use performance manager if available, otherwise fall back to config settings
perf_config = _get_performance_config()
POOL_SIZE = (
    perf_config.connection_pool_size if perf_config else settings.database.pool_size
)
MAX_OVERFLOW = (
    perf_config.connection_pool_size * 2
    if perf_config
    else settings.database.max_overflow
)
POOL_TIMEOUT = settings.database.pool_timeout
POOL_RECYCLE = settings.database.pool_recycle

logger.info(
    "Database URL: %s", DATABASE_URL.split("///")[0] + "///<path>",
)  # Log without exposing full path
logger.info("Connection pool size: %s", POOL_SIZE)

# --- Engine Configuration ---
engine_args: dict[str, Any] = {
    "echo": settings.database.echo,
    "future": True,  # Use SQLAlchemy 2.0 style
}

# Configure connection pooling based on database type
if "sqlite" not in DATABASE_URL:
    # PostgreSQL, MySQL, etc. - use standard connection pooling
    logger.info("Configuring standard connection pooling for non-SQLite database")
    engine_args.update(
        {
            "pool_size": POOL_SIZE,
            "max_overflow": MAX_OVERFLOW,
            "pool_pre_ping": True,
            "pool_recycle": POOL_RECYCLE,
            "pool_timeout": POOL_TIMEOUT,
        },
    )
else:
    # SQLite-specific optimizations
    logger.info("Configuring SQLite-specific optimizations")
    engine_args.update(
        {
            "poolclass": StaticPool,
            "connect_args": {
                "check_same_thread": False,  # Required for async SQLite
                "timeout": settings.database.connection_timeout,
            },
            # For SQLite, we use a single connection pool
            "pool_pre_ping": True,
        },
    )


# --- Create Engine ---
engine = create_async_engine(DATABASE_URL, **engine_args)

# --- Session Factory ---
# Optimized session factory with proper configuration for medical data handling
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects accessible after commit
    autocommit=False,  # Explicit transaction control
    autoflush=False,  # Manual flush control for better performance
)

# --- Declarative Base ---
Base = declarative_base()


# --- Database Utilities ---
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides a transactional database session.

    Features:
    - Automatic transaction management with rollback on errors
    - Proper session cleanup to prevent connection leaks
    - Optimized for medical data processing workflows
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Only commit if no exception occurred
            await session.commit()
        except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
            # Log the error for debugging (without PHI)
            logger.exception(
                "Database transaction failed, rolling back: %s", type(e).__name__,
            )
            await session.rollback()
            raise
        finally:
            # Ensure session is always closed
            await session.close()


async def init_db() -> None:
    """Initialize the database by creating all tables and applying optimizations.

    This function:
    - Creates all tables defined by SQLAlchemy models
    - Applies database-specific optimizations (SQLite pragmas, indexes)
    - Ensures proper schema setup for medical data compliance
    """
    logger.info("Initializing database schema")

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

        # Apply SQLite-specific optimizations if enabled
        if "sqlite" in DATABASE_URL and settings.database.sqlite_optimizations:
            logger.info("Applying SQLite performance optimizations")

            await conn.execute(
                text("PRAGMA journal_mode=WAL"),
            )  # Write-Ahead Logging for better concurrency
            await conn.execute(
                text("PRAGMA synchronous=NORMAL"),
            )  # Balance between safety and performance
            await conn.execute(
                text("PRAGMA cache_size=10000"),
            )  # Increase cache size (10MB)
            await conn.execute(
                text("PRAGMA temp_store=MEMORY"),
            )  # Store temp tables in memory
            await conn.execute(
                text("PRAGMA mmap_size=268435456"),
            )  # Use memory mapping (256MB)
            await conn.execute(
                text("PRAGMA foreign_keys=ON"),
            )  # Enable foreign key constraints

    logger.info("Database initialization complete")


async def close_db_connections() -> None:
    """Gracefully dispose of database engine and close all connections.

    This function ensures:
    - All active connections are properly closed
    - Connection pool is disposed of cleanly
    - No database locks remain after shutdown
    """
    logger.info("Shutting down database connections")
    try:
        await engine.dispose()
        logger.info("Database connections closed successfully")
    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        logger.exception("Error during database shutdown: %s", e)
        raise


async def get_db_health() -> dict[str, Any]:
    """Check database health and return status information.

    Returns:
        Dict containing database health metrics and status

    """
    try:
        async with AsyncSessionLocal() as session:
            # Simple query to test connectivity
            result = await session.execute(text("SELECT 1"))
            result.fetchone()

            # Get basic stats if SQLite
            stats: dict[str, Any] = {
                "status": "healthy",
                "engine": str(engine.url).split("://")[0],
            }

            if "sqlite" in DATABASE_URL:
                # Get SQLite-specific stats
                pragma_results = await session.execute(text("PRAGMA database_list"))
                stats["databases"] = len(pragma_results.fetchall())

            return stats

    except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
        logger.exception("Database health check failed: %s", e)
        return {"status": "unhealthy", "error": str(e)}


async def optimize_database() -> None:
    """Apply runtime database optimizations.

    This function can be called periodically to maintain optimal performance.
    """
    if "sqlite" not in DATABASE_URL or not settings.database.sqlite_optimizations:
        return

    try:
        async with AsyncSessionLocal() as session:
            logger.info("Running database optimization")

            # Analyze tables for better query planning
            await session.execute(text("ANALYZE"))

            # Vacuum if needed (reclaim space)
            result = await session.execute(text("PRAGMA auto_vacuum"))
            auto_vacuum = result.scalar()

            if auto_vacuum == 0:  # None
                await session.execute(text("VACUUM"))
                logger.info("Database vacuum completed")

            await session.commit()

    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as e:
        logger.exception("Database optimization failed: %s", e)


# --- Connection Management Utilities ---
async def test_connection() -> bool:
    """Test database connectivity.

    Returns:
        True if connection successful, False otherwise

    """
    try:
        health = await get_db_health()
        return health["status"] == "healthy"
    except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error):
        return False
