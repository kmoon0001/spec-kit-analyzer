#!/usr/bin/env python3
"""
Script to create a test user directly in the database.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database.database import get_async_db
from src.database import crud, schemas
from src.auth import AuthService

async def create_test_user():
    """Create a test user in the database."""
    print("👤 Creating Test User")
    print("=" * 50)
    
    # Get database session
    db_gen = get_async_db()
    db = await db_gen.__anext__()
    
    try:
        # Check if user already exists
        existing_user = await crud.get_user_by_username(db, "admin")
        if existing_user:
            print("   ℹ️ User 'admin' already exists")
            print(f"   User ID: {existing_user.id}")
            print(f"   Username: {existing_user.username}")
            print(f"   Is Active: {existing_user.is_active}")
            return True
        
        # Create auth service
        auth_service = AuthService()
        
        # Create user data
        user_data = schemas.UserCreate(
            username="admin",
            password="admin123",
            email="admin@example.com"
        )
        
        # Hash the password
        hashed_password = auth_service.get_password_hash(user_data.password)
        
        # Create user in database
        user = await crud.create_user(
            db=db,
            username=user_data.username,
            hashed_password=hashed_password,
            email=user_data.email
        )
        
        print("   ✅ Test user created successfully!")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   User ID: {user.id}")
        print("   Password: admin123")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating user: {e}")
        return False
        
    finally:
        await db.close()

if __name__ == "__main__":
    success = asyncio.run(create_test_user())
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Test user setup complete!")
        print("You can now use these credentials:")
        print("   Username: admin")
        print("   Password: admin123")
    else:
        print("❌ Failed to create test user!")