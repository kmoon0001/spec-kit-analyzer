import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Need to add project root to path for imports to work
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from src.models import User
from src.auth import AuthService
from src.config import get_settings

async def create_admin_user():
    settings = get_settings()
    DATABASE_URL = settings.database.url
    if "sqlite" in DATABASE_URL and "aiosqlite" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")

    engine = create_async_engine(DATABASE_URL)
    AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession)

    auth_service = AuthService()
    hashed_password = auth_service.get_password_hash("admin")

    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Check if user exists
            from sqlalchemy.future import select
            result = await session.execute(select(User).filter(User.username == "admin"))
            db_user = result.scalars().first()

            if not db_user:
                new_user = User(
                    username="admin",
                    email="admin@example.com",
                    hashed_password=hashed_password,
                    is_active=True,
                    is_admin=True,
                    license_key="ADMIN-LICENSE-KEY"
                )
                session.add(new_user)
                print("Admin user created.")
            else:
                print("Admin user already exists.")

if __name__ == "__main__":
    asyncio.run(create_admin_user())