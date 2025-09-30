import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from ..config import get_settings

logger = logging.getLogger(__name__)

# --- Database Configuration ---
settings = get_settings()
DATABASE_URL = settings.database.url

# Ensure the URL is async-compatible for SQLite
if "sqlite" in DATABASE_URL and "aiosqlite" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")

# --- Performance-Tuned Async Engine ---
# Centralized, high-performance engine with connection pooling.
try:
    # Attempt to use performance settings if available
    from ..core.performance_manager import get_performance_config
    perf_config = get_performance_config()
    pool_size = perf_config.connection_pool_size
    logger.info("Applying performance-tuned connection pool size: %d", pool_size)
except (ImportError, AttributeError):
    pool_size = 10  # Sensible default
    logger.info("Using default connection pool size: %d", pool_size)

engine = create_async_engine(
    DATABASE_URL,
    pool_size=pool_size,
    max_overflow=pool_size * 2,
    pool_pre_ping=True,  # Checks connection validity before use
    pool_recycle=3600,   # Recycles connections every hour
    echo=settings.database.echo,  # Controlled by config
)

# --- Session Factory ---
# A single, configured session factory for the entire application.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# --- Declarative Base ---
Base = declarative_base()

# --- Database Utilities ---
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a transactional database session.
    Ensures the session is always closed, even in case of errors.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initializes the database by creating all tables defined by Base's metadata.
    This is typically called once on application startup.
    """
    logger.info("Initializing database and creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialization complete.")


async def close_db_connections():
    """
    Gracefully disposes of the database engine's connection pool.
    This should be called on application shutdown.
    """
    logger.info("Closing database connections...")
    await engine.dispose()
    logger.info("Database connections closed.")
