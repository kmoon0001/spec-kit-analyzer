from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import get_settings

settings = get_settings()

# Ensure the URL is async-compatible (e.g., "sqlite+aiosqlite:///./compliance.db")
DATABASE_URL = settings.database.url
if "sqlite" in DATABASE_URL and "aiosqlite" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")

engine = create_async_engine(DATABASE_URL)

# expire_on_commit=False is important for async sessions
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_async_db() -> AsyncSession:
    """
    Dependency that provides an async database session.
    """
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    """
    Initializes the database, creating all tables defined by Base's metadata.
    """
    async with engine.begin() as conn:
        # For SQLite, metadata.create_all is a blocking operation.
        # To run it in an async context, we use run_sync.
        await conn.run_sync(Base.metadata.create_all)
