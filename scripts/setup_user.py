#!/usr/bin/env python3
"""Create a default user for testing."""

import asyncio
import sys

sys.path.insert(0, ".")


async def setup_user():
    from src import crud
    from src.auth import AuthService
    from src.database import init_db
    from src.database.database import get_async_db
    from src.database.schemas import UserCreate

    print("Initializing database...")
    await init_db()

    print("Checking for existing users...")
    async for db_session in get_async_db():
        # Try to find existing user
        existing_user = await crud.get_user_by_username(db_session, "admin")

        if existing_user:
            print("✅ User 'admin' already exists")
        else:
            print("Creating default admin user...")
            # Create default user
            user_data = UserCreate(username="admin", password="admin123", is_admin=True)

            hashed_password = AuthService.get_password_hash("admin123")
            new_user = await crud.create_user(db_session, user_data, hashed_password, is_admin=True)
            await db_session.commit()

            print(f"✅ Created user: {new_user.username}")
            print("   Username: admin")
            print("   Password: admin123")

        break


if __name__ == "__main__":
    asyncio.run(setup_user())
