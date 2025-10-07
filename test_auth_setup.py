#!/usr/bin/env python3
"""
Test script to check authentication setup and create a test user if needed.
"""

import sys
import requests
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

API_URL = "http://127.0.0.1:8001"

def test_auth_endpoints():
    """Test authentication endpoints."""
    print("🔐 Testing Authentication Setup")
    print("=" * 50)
    
    # Test if auth endpoints exist
    print("\n1️⃣ Testing auth endpoint availability...")
    
    try:
        # Test token endpoint with invalid credentials
        response = requests.post(
            f"{API_URL}/auth/token",
            data={
                "username": "nonexistent",
                "password": "invalid"
            },
            timeout=10
        )
        
        print(f"   Token endpoint status: {response.status_code}")
        if response.status_code == 404:
            print("   ❌ Auth token endpoint not found")
            return False
        elif response.status_code in [400, 401, 422]:
            print("   ✅ Auth token endpoint exists (expected error for invalid credentials)")
        else:
            print(f"   ⚠️ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error testing auth endpoint: {e}")
        return False
    
    # Test creating a user (if endpoint exists)
    print("\n2️⃣ Testing user creation...")
    
    try:
        # Try to create a test user
        response = requests.post(
            f"{API_URL}/auth/register",  # Common endpoint name
            json={
                "username": "admin",
                "password": "admin123",
                "email": "admin@example.com"
            },
            timeout=10
        )
        
        print(f"   Register endpoint status: {response.status_code}")
        if response.status_code == 404:
            print("   ⚠️ Register endpoint not found - may need manual user creation")
        elif response.status_code in [200, 201]:
            print("   ✅ User created successfully")
        elif response.status_code == 400:
            print("   ℹ️ User may already exist")
        else:
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error testing register endpoint: {e}")
    
    # Test login with common credentials
    print("\n3️⃣ Testing login with common credentials...")
    
    common_credentials = [
        ("admin", "admin123"),
        ("admin", "admin"),
        ("test", "test"),
        ("user", "password")
    ]
    
    for username, password in common_credentials:
        try:
            response = requests.post(
                f"{API_URL}/auth/token",
                data={
                    "username": username,
                    "password": password
                },
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                print(f"   ✅ Login successful with {username}:{password}")
                print(f"   Token: {token_data.get('access_token', 'N/A')[:20]}...")
                return True
            else:
                print(f"   ❌ Login failed for {username}:{password} - {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error testing login {username}:{password}: {e}")
    
    return False

if __name__ == "__main__":
    success = test_auth_endpoints()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Authentication test PASSED!")
        print("Found working credentials for API access.")
    else:
        print("❌ Authentication test FAILED!")
        print("No working credentials found.")
        print("\n💡 Next steps:")
        print("• Check if users exist in the database")
        print("• Create a test user manually")
        print("• Verify auth router configuration")