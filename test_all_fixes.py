"""Comprehensive test to verify all debugging fixes."""
import asyncio
import sys
from src.database.database import get_async_db
from src.database import crud
from src.auth import AuthService
from src.core.cleanup_services import CleanupManager
from src.core.session_manager import get_session_manager
from src.core.enhanced_session_manager import get_session_manager as get_enhanced_session_manager

auth_service = AuthService()

async def test_login():
    """Test 1: Login functionality."""
    print("\n[TEST 1] Testing login...")

    async for db in get_async_db():
        try:
            user = await crud.get_user_by_username(db, "admin")

            if not user:
                print("[FAIL] User 'admin' not found in database!")
                return False

            print(f"[PASS] Found user: {user.username}, ID: {user.id}")

            # Test password
            password = "admin123"
            is_valid = auth_service.verify_password(password, user.hashed_password)

            if is_valid:
                print(f"[PASS] Password verification successful!")

                # Create token
                from datetime import timedelta
                token = auth_service.create_access_token(
                    data={"sub": user.username},
                    expires_delta=timedelta(minutes=30)
                )
                print(f"[PASS] Token created: {token[:30]}...")
                return True
            else:
                print(f"[FAIL] Password verification failed!")
                return False

        except Exception as e:
            print(f"[FAIL] Exception: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await db.close()
            break

def test_session_manager():
    """Test 2: SessionManager cleanup method exists."""
    print("\n[TEST 2] Testing SessionManager...")

    try:
        session_manager = get_session_manager()

        # Check if the correct method exists
        if hasattr(session_manager, '_cleanup_expired_sessions'):
            print("[PASS] SessionManager has _cleanup_expired_sessions method")

            # Test cleanup doesn't crash
            session_manager._cleanup_expired_sessions()
            print("[PASS] SessionManager cleanup executed successfully")
            return True
        else:
            print("[FAIL] SessionManager missing _cleanup_expired_sessions method")
            return False

    except Exception as e:
        print(f"[FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_session_manager():
    """Test 3: EnhancedSessionManager create_session with correct args."""
    print("\n[TEST 3] Testing EnhancedSessionManager...")

    try:
        session_manager = get_enhanced_session_manager()

        # Create a test session with individual arguments
        session_id = session_manager.create_session(
            user_id=1,
            username="test_user",
            ip_address="127.0.0.1",
            user_agent="Test Agent",
            login_method="password"
        )

        print(f"[PASS] Session created: {session_id[:20]}...")

        # Validate the session
        session_info = session_manager.validate_session(session_id, "127.0.0.1")

        if session_info:
            print(f"[PASS] Session validated successfully")

            # Cleanup
            session_manager.invalidate_session(session_id)
            print(f"[PASS] Session invalidated successfully")
            return True
        else:
            print(f"[FAIL] Session validation failed")
            return False

    except Exception as e:
        print(f"[FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_cleanup_service():
    """Test 4: Session cleanup service fix."""
    print("\n[TEST 4] Testing Session cleanup fix...")

    try:
        from src.core.cleanup_services import SessionCleanupService

        # Create session cleanup service with correct signature
        cleanup_service = SessionCleanupService(max_age_hours=24)

        # Test session cleanup - this was calling the wrong method before
        await cleanup_service._run_cleanup()
        print("[PASS] Session cleanup executed without errors (method name fixed!)")
        return True

    except Exception as e:
        print(f"[FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_input_validation_middleware():
    """Test 5: InputValidationMiddleware is properly configured."""
    print("\n[TEST 5] Testing InputValidationMiddleware...")

    try:
        from src.api.middleware.input_validation import InputValidationMiddleware

        # Check middleware has correct methods
        middleware = InputValidationMiddleware(app=None)

        # Test content type validation
        is_valid = middleware._is_valid_content_type("application/json")
        if is_valid:
            print("[PASS] Content type validation working")
        else:
            print("[FAIL] Content type validation failed")
            return False

        # Test form data is supported
        is_valid = middleware._is_valid_content_type("application/x-www-form-urlencoded")
        if is_valid:
            print("[PASS] Form data content type supported")
            return True
        else:
            print("[FAIL] Form data content type not supported")
            return False

    except Exception as e:
        print(f"[FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("="*60)
    print("COMPREHENSIVE DEBUGGING VERIFICATION")
    print("="*60)

    results = []

    # Run tests
    results.append(await test_login())
    results.append(test_session_manager())
    results.append(test_enhanced_session_manager())
    results.append(await test_cleanup_service())
    results.append(test_input_validation_middleware())

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    # Filter out None values (if any)
    results = [r for r in results if r is not None]
    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if passed == total:
        print("\n[SUCCESS] ALL TESTS PASSED!")
        return True
    else:
        print(f"\n[FAILED] {total - passed} TEST(S) FAILED")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
