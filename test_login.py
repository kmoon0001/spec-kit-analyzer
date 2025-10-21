"""Test login endpoint directly."""
import asyncio
import sys
from src.database.database import get_async_db
from src.database import crud
from src.auth import AuthService

auth_service = AuthService()

async def test_login():
    """Test login with admin user."""
    print("[*] Testing login...")

    async for db in get_async_db():
        try:
            # Get user
            user = await crud.get_user_by_username(db, "admin")

            if not user:
                print("[ERROR] User 'admin' not found in database!")
                return False

            print(f"[OK] Found user: {user.username}, ID: {user.id}, Active: {user.is_active}")

            # Test password
            password = "admin123"
            is_valid = auth_service.verify_password(password, user.hashed_password)

            if is_valid:
                print(f"[OK] Password verification successful!")

                # Create token
                from datetime import timedelta
                token = auth_service.create_access_token(
                    data={"sub": user.username},
                    expires_delta=timedelta(minutes=30)
                )
                print(f"[OK] Token created: {token[:50]}...")
                return True
            else:
                print(f"[ERROR] Password verification failed!")
                return False

        except Exception as e:
            print(f"[ERROR] Exception: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await db.close()
            break

if __name__ == "__main__":
    result = asyncio.run(test_login())
    if result:
        print("[SUCCESS] All tests passed!")
        sys.exit(0)
    else:
        print("[FAILED] Tests failed!")
        sys.exit(1)
