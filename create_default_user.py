import asyncio
from src.database.database import AsyncSessionLocal
from src.database import models, crud
from src.auth import AuthService

async def create_default_user():
    """
    Creates a default administrative user if one does not already exist.
    """
    db = AsyncSessionLocal()
    try:
        username = "admin"
        password = "password"

        # Check if the user already exists
        existing_user = await crud.get_user_by_username(db, username=username)
        if existing_user:
            print(f"User '{username}' already exists. No action taken.")
            return

        print(f"Creating default admin user '{username}'...")

        # Hash the password using the static method from AuthService
        hashed_password = AuthService.get_password_hash(password)

        # Create the user directly using the model
        db_user = models.User(
            username=username,
            hashed_password=hashed_password,
            is_admin=True,
            is_active=True,
            license_key=None
        )

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        print(f"Successfully created user '{username}' with password '{password}'.")
        print("Please consider changing this password for security reasons.")

    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(create_default_user())