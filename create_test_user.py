"""Create a test user for development."""
import asyncio
from src.database.database import get_async_db, init_db
from src.database import crud, models, schemas
from src.auth import AuthService

auth_service = AuthService()


async def create_test_user():
    """Create a test user account."""
    print("[*] Initializing database...")
    # Initialize database
    await init_db()
    print("[OK] Database initialized")

    # Get database session
    async for db in get_async_db():
        try:
            print("[*] Checking for existing user...")
            # Check if user already exists
            from sqlalchemy import select
            result = await db.execute(
                select(models.User).where(models.User.username == "admin")
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print("[OK] User 'admin' already exists!")
                print(f"   User ID: {existing_user.id}")
                print(f"   Username: {existing_user.username}")
                return

            # Create new user
            user = models.User(
                username="admin",
                hashed_password=auth_service.get_password_hash("admin123"),
                is_active=True,
                is_admin=True
            )

            db.add(user)
            await db.commit()
            await db.refresh(user)

            print("[OK] Test user created successfully!")
            print(f"   Username: admin")
            print(f"   Password: admin123")
            print(f"   User ID: {user.id}")
            print(f"\n[*] You can now login with these credentials in the browser")

        except Exception as e:
            print(f"[ERROR] Error creating user: {e}")
            await db.rollback()
            raise
        finally:
            await db.close()
            break


if __name__ == "__main__":
    asyncio.run(create_test_user())
