#!/usr/bin/env python3
"""
Wait for server to come online and test endpoints
"""

import requests
import time
import sys

def wait_for_server():
    """Wait for server to come online and test endpoints"""
    print("⏳ Waiting for API server to start...")
    print("   (Restart server with: python scripts/run_api.py)")
    print("=" * 50)
    
    attempt = 1
    max_attempts = 60  # Wait up to 5 minutes
    
    while attempt <= max_attempts:
        try:
            print(f"\r🔍 Attempt {attempt}/{max_attempts}: Testing connection...", end="", flush=True)
            
            # Test basic connectivity
            response = requests.get("http://127.0.0.1:8001/", timeout=2)
            
            if response.status_code == 200:
                print(f"\n✅ Server is online! Testing new endpoints...")
                
                # Test all endpoints
                endpoints = [
                    ("GET", "/", "Root endpoint"),
                    ("GET", "/health", "Health check"),
                    ("GET", "/rubrics", "NEW: Rubrics list"),
                    ("GET", "/ai/status", "NEW: AI status")
                ]
                
                all_working = True
                for method, path, description in endpoints:
                    try:
                        resp = requests.get(f"http://127.0.0.1:8001{path}", timeout=5)
                        if resp.status_code == 200:
                            print(f"   ✅ {path} - Working!")
                            if "NEW:" in description:
                                print(f"      🎉 NEW ENDPOINT SUCCESS!")
                        else:
                            print(f"   ❌ {path} - Failed ({resp.status_code})")
                            all_working = False
                    except Exception as e:
                        print(f"   ❌ {path} - Error: {e}")
                        all_working = False
                
                if all_working:
                    print(f"\n🎉 ALL ENDPOINTS WORKING!")
                    print(f"   Ready to start GUI: python scripts/run_gui.py")
                    return True
                else:
                    print(f"\n⚠️  Some endpoints have issues")
                    return False
                    
        except requests.exceptions.ConnectionError:
            # Server not ready yet
            pass
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
        
        time.sleep(5)  # Wait 5 seconds between attempts
        attempt += 1
    
    print(f"\n❌ Timeout waiting for server after {max_attempts} attempts")
    print(f"   Make sure to start: python scripts/run_api.py")
    return False

if __name__ == "__main__":
    success = wait_for_server()
    sys.exit(0 if success else 1)