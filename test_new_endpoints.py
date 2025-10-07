#!/usr/bin/env python3
"""
Test the newly added endpoints to make sure they work
"""

import requests
import sys

API_URL = "http://127.0.0.1:8001"

def test_new_endpoints():
    """Test all the newly added endpoints"""
    print("🧪 Testing New Endpoints")
    print("=" * 40)
    
    endpoints_to_test = [
        {
            "method": "GET",
            "path": "/health",
            "description": "Health check (existing)"
        },
        {
            "method": "GET", 
            "path": "/rubrics",
            "description": "Get rubrics (NEW)"
        },
        {
            "method": "GET",
            "path": "/ai/status", 
            "description": "AI status (NEW)"
        }
    ]
    
    results = []
    
    for endpoint in endpoints_to_test:
        print(f"\n🔍 Testing {endpoint['method']} {endpoint['path']}")
        print(f"   {endpoint['description']}")
        
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(f"{API_URL}{endpoint['path']}", timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS - Status: {response.status_code}")
                print(f"   📄 Response: {response.json()}")
                results.append(True)
            else:
                print(f"   ❌ FAILED - Status: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                results.append(False)
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ CONNECTION ERROR - Server not running")
            results.append(False)
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append(False)
    
    print(f"\n📊 Results:")
    print(f"   Passed: {sum(results)}/{len(results)}")
    print(f"   Success Rate: {sum(results)/len(results)*100:.1f}%")
    
    if all(results):
        print("   🎉 All endpoints working!")
        return True
    else:
        print("   ⚠️  Some endpoints need attention")
        return False

if __name__ == "__main__":
    success = test_new_endpoints()
    sys.exit(0 if success else 1)