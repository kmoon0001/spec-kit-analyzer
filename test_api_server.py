#!/usr/bin/env python3
"""
Test script to verify the API server is running and accessible.
"""

import sys
import requests
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

API_URL = "http://127.0.0.1:8001"

def test_api_server():
    """Test API server accessibility and endpoints."""
    print("🌐 Testing API Server")
    print("=" * 50)
    
    # Test 1: Basic connectivity
    print("\n1️⃣ Testing basic connectivity...")
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        print(f"   Root endpoint status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
            print("   ✅ API server is running and accessible")
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Cannot connect to API server: {e}")
        print("   💡 Make sure the API server is running with: python scripts/run_api.py")
        return False
    
    # Test 2: Check available endpoints
    print("\n2️⃣ Testing specific endpoints...")
    
    endpoints_to_test = [
        ("/health", "GET", "Health check"),
        ("/auth/token", "POST", "Auth token"),
        ("/analysis/analyze", "POST", "Analysis submission"),
        ("/docs", "GET", "API documentation"),
    ]
    
    for endpoint, method, description in endpoints_to_test:
        try:
            if method == "GET":
                response = requests.get(f"{API_URL}{endpoint}", timeout=5)
            else:
                # For POST endpoints, send empty data to see if endpoint exists
                response = requests.post(f"{API_URL}{endpoint}", json={}, timeout=5)
            
            print(f"   {method} {endpoint} ({description}): {response.status_code}")
            
            if response.status_code == 404:
                print("      ❌ Endpoint not found")
            elif response.status_code in [200, 400, 401, 422]:
                print("      ✅ Endpoint exists (expected error for invalid data)")
            else:
                print(f"      ⚠️ Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error testing {endpoint}: {e}")
    
    # Test 3: Check FastAPI docs
    print("\n3️⃣ Testing FastAPI documentation...")
    try:
        response = requests.get(f"{API_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("   ✅ FastAPI docs accessible at /docs")
            print("   💡 You can view all endpoints at http://127.0.0.1:8001/docs")
        else:
            print(f"   ❌ Docs not accessible: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error accessing docs: {e}")
    
    return True

if __name__ == "__main__":
    success = test_api_server()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 API server test completed!")
        print("Check the endpoint results above for specific issues.")
    else:
        print("❌ API server is not accessible!")
        print("Start the server with: python scripts/run_api.py")