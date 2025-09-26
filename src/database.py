<<<<<<< HEAD
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
# Get the database URL from the environment variable
import os
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./compliance.db")
DATABASE_PATH = DATABASE_URL
||||||| c46cdd8
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get the database URL from the environment variable
import os
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./compliance.db")
DATABASE_PATH = DATABASE_URL
=======
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import get_settings

settings = get_settings()
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> origin/main
||||||| 604b275
=======
||||||| 24e8eb0
# Get the database URL from the environment variable
import os
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./compliance.db")
=======
settings = get_settings()
>>>>>>> origin/main
>>>>>>> origin/main
||||||| 278fb88
||||||| 24e8eb0
# Get the database URL from the environment variable
import os
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./compliance.db")
=======
settings = get_settings()
>>>>>>> origin/main
=======
>>>>>>> origin/main

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
    """Dependency that provides an async database session."""
    async with AsyncSessionLocal() as session:
        yield session

<<<<<<< HEAD
def init_db():
    Base.metadata.create_all(bind=engine)
||||||| c46cdd8
def init_db():
    Base.metadata.create_all(bind=engine)
=======
async def init_db():
    """Initializes the database, creating all tables defined by Base's metadata."""
    async with engine.begin() as conn:
        # For SQLite, metadata.create_all is a blocking operation.
        # To run it in an async context, we use run_sync.
<<<<<<< HEAD
        await conn.run_sync(Base.metadata.create_all)
>>>>>>> origin/main
||||||| 278fb88
        await conn.run_sync(Base.metadata.create_all)
=======
        await conn.run_sync(Base.metadata.create_all)
>>>>>>> origin/main
