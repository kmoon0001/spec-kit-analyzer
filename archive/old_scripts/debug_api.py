#!/usr/bin/env python3
"""
Debug API startup issues
"""

import os
import sys
import time
import traceback

# Set environment for testing
os.environ["USE_AI_MOCKS"] = "true"
os.environ["API_PORT"] = "8100"

def test_imports():
    """Test if we can import the API components"""
    print("Testing imports...")
    
    try:
        print("  Importing FastAPI...")
        import fastapi
        print(f"  ✓ FastAPI {fastapi.__version__}")
        
        print("  Importing uvicorn...")
        import uvicorn
        print(f"  ✓ Uvicorn {uvicorn.__version__}")
        
        print("  Importing src.config...")
        from src.config import get_settings
        settings = get_settings()
        print(f"  ✓ Config loaded, API port: {settings.port}")
        
        print("  Importing src.api.main...")
        from src.api.main import app
        print("  ✓ FastAPI app imported")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        traceback.print_exc()
        return False

def test_basic_startup():
    """Test basic API startup"""
    print("\nTesting basic API startup...")
    
    try:
        from src.api.main import app
        import uvicorn
        
        print("  Creating uvicorn config...")
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=8100,
            log_level="debug",
            access_log=True
        )
        
        print("  Creating server...")
        server = uvicorn.Server(config)
        
        print("  ✓ Server created successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Server creation failed: {e}")
        traceback.print_exc()
        return False

def test_database():
    """Test database connection"""
    print("\nTesting database...")
    
    try:
        print("  Importing database modules...")
        from src.database.database import get_database_url
        
        db_url = get_database_url()
        print(f"  ✓ Database URL: {db_url}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Database test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Main debug function"""
    print("=" * 60)
    print("API DEBUG DIAGNOSTICS")
    print("=" * 60)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test basic startup
    if not test_basic_startup():
        success = False
    
    # Test database
    if not test_database():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✓ ALL TESTS PASSED - API should be able to start")
    else:
        print("✗ SOME TESTS FAILED - Check errors above")
    print("=" * 60)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())