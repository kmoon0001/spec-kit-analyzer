#!/usr/bin/env python3
"""
Test script to directly test the auth endpoint using FastAPI TestClient.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_auth_direct():
    """Test auth endpoint directly using FastAPI TestClient."""
    print("🔐 Testing Auth Endpoint Directly")
    print("=" * 50)
    
    try:
        from fastapi.testclient import TestClient
        from src.api.main import app
        
        client = TestClient(app)
        
        print("\n1️⃣ Testing auth token endpoint...")
        
        # Test with invalid credentials first
        response = client.post(
            "/auth/token",
            data={
                "username": "invalid",
                "password": "invalid"
            }
        )
        
        print(f"   Status code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 404:
            print("   ❌ Auth endpoint not found in FastAPI app")
            return False
        elif response.status_code in [400, 401, 422]:
            print("   ✅ Auth endpoint exists (expected error for invalid credentials)")
        
        # Test with valid credentials
        print("\n2️⃣ Testing with valid credentials...")
        response = client.post(
            "/auth/token",
            data={
                "username": "admin",
                "password": "admin123"
            }
        )
        
        print(f"   Status code: {response.status_code}")
        if response.status_code == 200:
            token_data = response.json()
            print("   ✅ Authentication successful!")
            print(f"   Token type: {token_data.get('token_type')}")
            print(f"   Access token: {token_data.get('access_token', 'N/A')[:20]}...")
            return True
        else:
            print(f"   ❌ Authentication failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing auth endpoint: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_auth_direct()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Auth endpoint test PASSED!")
        print("The auth endpoint works when tested directly.")
    else:
        print("❌ Auth endpoint test FAILED!")
        print("There's an issue with the auth router registration.")