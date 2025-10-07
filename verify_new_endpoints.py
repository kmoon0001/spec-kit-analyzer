#!/usr/bin/env python3
"""
Verify that the new endpoints are working after server restart
"""

import requests
import time

def test_endpoints_after_restart():
    """Test the new endpoints after server restart"""
    print("🔄 Verifying New Endpoints After Server Restart")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    print("⏳ Waiting 3 seconds for server to be ready...")
    time.sleep(3)
    
    endpoints = [
        ("GET", "/", "Root endpoint"),
        ("GET", "/health", "Health check"),
        ("GET", "/rubrics", "NEW: Rubrics list"),
        ("GET", "/ai/status", "NEW: AI status")
    ]
    
    for method, path, description in endpoints:
        try:
            print(f"\n🔍 Testing {method} {path}")
            print(f"   {description}")
            
            response = requests.get(f"http://127.0.0.1:8001{path}", timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS - {response.status_code}")
                if path in ["/rubrics", "/ai/status"]:
                    print(f"   🎉 NEW ENDPOINT WORKING!")
                # Show first part of response
                resp_text = str(response.json())
                if len(resp_text) > 100:
                    resp_text = resp_text[:100] + "..."
                print(f"   📄 Response: {resp_text}")
            else:
                print(f"   ❌ FAILED - {response.status_code}")
                print(f"   📄 Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ CONNECTION ERROR - Server not running")
            print(f"   💡 Make sure to restart: python scripts/run_api.py")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. If endpoints work: Start GUI with 'python scripts/run_gui.py'")
    print(f"   2. If connection errors: Restart server with 'python scripts/run_api.py'")

if __name__ == "__main__":
    test_endpoints_after_restart()