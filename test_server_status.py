#!/usr/bin/env python3
"""
Quick server status test - checks if the API server is responding
"""

import requests
import sys

def test_server_status():
    """Test if the API server is responding"""
    try:
        print("🔍 Testing API server status...")
        response = requests.get("http://127.0.0.1:8001/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ API server is responding!")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ API server returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        print("   Make sure the server is running: python scripts/run_api.py")
        return False
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

if __name__ == "__main__":
    success = test_server_status()
    sys.exit(0 if success else 1)