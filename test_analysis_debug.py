#!/usr/bin/env python3
"""
Test analysis with debugging to see what's happening
"""

import requests
import time
import json

def test_analysis_with_debug():
    """Test analysis with detailed debugging"""
    print("🔍 Testing Analysis with Debug Info")
    print("=" * 50)
    
    # First, let's check what tasks are currently running
    print("\n1️⃣ Checking current tasks...")
    try:
        # This will require auth, but let's see what error we get
        response = requests.get("http://127.0.0.1:8001/analysis/all-tasks", timeout=5)
        print(f"   All tasks response: {response.status_code}")
        if response.status_code == 401:
            print("   ⚠️  Authentication required (expected)")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Check if we can see any task status
    print("\n2️⃣ Checking specific task status...")
    try:
        # Try to check a task status (will need auth)
        response = requests.get("http://127.0.0.1:8001/analysis/status/analysis_1759878713", timeout=5)
        print(f"   Task status response: {response.status_code}")
        if response.status_code == 401:
            print("   ⚠️  Authentication required (expected)")
        elif response.status_code == 404:
            print("   ❌ Task not found - might have expired or failed")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print(f"\n🔍 Analysis Issues Likely Causes:")
    print(f"   1. ✅ Background task async/sync mismatch (FIXED)")
    print(f"   2. ⚠️  Authentication token not being sent properly")
    print(f"   3. ⚠️  Analysis service taking too long")
    print(f"   4. ⚠️  Memory/resource constraints")
    
    print(f"\n💡 Next Steps:")
    print(f"   • Restart API server to apply the fix")
    print(f"   • Check GUI authentication token handling")
    print(f"   • Monitor server logs during analysis")

if __name__ == "__main__":
    test_analysis_with_debug()