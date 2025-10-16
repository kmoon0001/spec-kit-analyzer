#!/usr/bin/env python3
"""
Simple API startup test script
"""

import asyncio
import os
import sys
import time
from pathlib import Path

import requests


async def test_api_startup():
    """Test if the API can start and respond to health checks."""
    print("Testing API startup...")
    
    # Set environment variables
    os.environ["API_PORT"] = "8100"
    os.environ["USE_AI_MOCKS"] = "true"  # Use mocks for faster startup
    
    # Import and start the API
    try:
        from src.api.main import app
        import uvicorn
        
        print("✓ API imports successful")
        
        # Test basic health endpoint
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=8100,
            log_level="info",
            access_log=False
        )
        
        server = uvicorn.Server(config)
        
        # Start server in background
        print("Starting API server...")
        task = asyncio.create_task(server.serve())
        
        # Wait a bit for server to start
        await asyncio.sleep(3)
        
        # Test health endpoint
        try:
            response = requests.get("http://127.0.0.1:8100/health", timeout=5)
            if response.status_code == 200:
                print("✓ API health check successful")
                print(f"Response: {response.json()}")
            else:
                print(f"✗ API health check failed: {response.status_code}")
        except requests.RequestException as e:
            print(f"✗ API health check failed: {e}")
        
        # Test root endpoint
        try:
            response = requests.get("http://127.0.0.1:8100/", timeout=5)
            if response.status_code == 200:
                print("✓ API root endpoint successful")
                print(f"Response: {response.json()}")
            else:
                print(f"✗ API root endpoint failed: {response.status_code}")
        except requests.RequestException as e:
            print(f"✗ API root endpoint failed: {e}")
        
        # Stop server
        server.should_exit = True
        await task
        
        print("✓ API test completed")
        
    except Exception as e:
        print(f"✗ API startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """Main entry point."""
    print("=" * 50)
    print("API Startup Test")
    print("=" * 50)
    
    try:
        result = asyncio.run(test_api_startup())
        if result:
            print("\n✓ All tests passed!")
            return 0
        else:
            print("\n✗ Some tests failed!")
            return 1
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())