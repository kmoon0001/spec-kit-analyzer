#!/usr/bin/env python3
"""
Debug analysis status - check what's happening with the analysis
"""

import requests
import time

def debug_analysis_status():
    """Debug the analysis status and see what's happening"""
    print("🔍 Debugging Analysis Status")
    print("=" * 40)
    
    # Check if the analysis endpoint exists and is working
    print("\n1️⃣ Testing Analysis Submit Endpoint...")
    try:
        # Test with a simple request to see if endpoint responds
        response = requests.get("http://127.0.0.1:8001/analysis/status/test", timeout=10)
        print(f"   Status endpoint response: {response.status_code}")
        if response.status_code == 401:
            print("   ⚠️  Authentication required - this is expected")
        elif response.status_code == 404:
            print("   ❌ Status endpoint not found")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Check server logs or status
    print("\n2️⃣ Checking Server Health...")
    try:
        response = requests.get("http://127.0.0.1:8001/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Server healthy: {data}")
        else:
            print(f"   ❌ Server health issue: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
    
    # Check AI status
    print("\n3️⃣ Checking AI Model Status...")
    try:
        response = requests.get("http://127.0.0.1:8001/ai/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ AI Status: {data.get('status')}")
            models = data.get('models', {})
            for model, status in models.items():
                print(f"   📊 {model}: {status}")
        else:
            print(f"   ❌ AI status issue: {response.status_code}")
    except Exception as e:
        print(f"   ❌ AI status check failed: {e}")
    
    print(f"\n🔍 Possible Issues:")
    print(f"   1. Analysis taking too long (AI processing)")
    print(f"   2. Missing authentication token")
    print(f"   3. Background task not completing")
    print(f"   4. Memory/resource constraints")
    print(f"   5. File processing error")
    
    print(f"\n💡 Debugging Steps:")
    print(f"   • Check API server logs for errors")
    print(f"   • Verify AI models are fully loaded")
    print(f"   • Check system memory usage")
    print(f"   • Try with a smaller test file")

if __name__ == "__main__":
    debug_analysis_status()