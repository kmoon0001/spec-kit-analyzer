"""
Create a test user for the Therapy Compliance Analyzer.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import AsyncSessionLocal, init_db
from src.database.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_user():
    """Create a test user with known credentials."""
    # Initialize database
    await init_db()
    
    # Create session
    async with AsyncSessionLocal() as session:
        # Check if user exists
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == "admin"))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("Admin user already exists. Updating password...")
            existing_user.hashed_password = pwd_context.hash("admin123")
            existing_user.is_admin = True
        else:
            print("Creating new admin user...")
            new_user = User(
                username="admin",
                hashed_password=pwd_context.hash("admin123"),
                is_admin=True
            )
            session.add(new_user)
        
        await session.commit()
        print("\n" + "="*50)
        print("✓ Test user created successfully!")
        print("="*50)
        print("Username: admin")
        print("Password: admin123")
        print("="*50)

if __name__ == "__main__":
    asyncio.run(create_test_user())
