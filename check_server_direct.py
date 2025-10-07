#!/usr/bin/env python3
"""
Direct server check - bypasses any connection issues
"""

import requests
import json

def check_server_direct():
    """Check server directly with detailed error info"""
    print("🔍 Direct Server Check")
    print("=" * 30)
    
    try:
        print("Testing basic connection...")
        response = requests.get("http://127.0.0.1:8001/", timeout=10)
        print(f"✅ Root endpoint: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        print("\nTesting NEW rubrics endpoint...")
        response = requests.get("http://127.0.0.1:8001/rubrics", timeout=10)
        print(f"✅ Rubrics endpoint: {response.status_code}")
        if response.status_code == 200:
            print("   🎉 NEW ENDPOINT WORKING!")
            data = response.json()
            print(f"   Found {len(data.get('rubrics', []))} rubrics")
        else:
            print(f"   ❌ Failed: {response.text}")
            
        print("\nTesting NEW AI status endpoint...")
        response = requests.get("http://127.0.0.1:8001/ai/status", timeout=10)
        print(f"✅ AI Status endpoint: {response.status_code}")
        if response.status_code == 200:
            print("   🎉 NEW ENDPOINT WORKING!")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Failed: {response.text}")
            
        return True
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        print("   Server may not be running or on different port")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_server_direct()