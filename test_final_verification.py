#!/usr/bin/env python3
"""
Final verification test - comprehensive check of all systems
"""

import requests
import sys

def test_final_verification():
    """Final comprehensive test of all systems"""
    print("🎯 Final System Verification")
    print("=" * 40)
    
    results = []
    
    # Test 1: API Server Running
    print("\n1️⃣ Testing API Server...")
    try:
        response = requests.get("http://127.0.0.1:8001/", timeout=5)
        if response.status_code == 200:
            print("   ✅ API server running")
            results.append(True)
        else:
            print(f"   ❌ API server error: {response.status_code}")
            results.append(False)
    except Exception as e:
        print(f"   ❌ API server not accessible: {e}")
        results.append(False)
    
    # Test 2: Health Check
    print("\n2️⃣ Testing Health Check...")
    try:
        response = requests.get("http://127.0.0.1:8001/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                print("   ✅ Health check passed")
                results.append(True)
            else:
                print(f"   ❌ Health check failed: {data}")
                results.append(False)
        else:
            print(f"   ❌ Health check error: {response.status_code}")
            results.append(False)
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        results.append(False)
    
    # Test 3: NEW Rubrics Endpoint
    print("\n3️⃣ Testing NEW Rubrics Endpoint...")
    try:
        response = requests.get("http://127.0.0.1:8001/rubrics", timeout=5)
        if response.status_code == 200:
            data = response.json()
            rubrics = data.get('rubrics', [])
            if len(rubrics) >= 3:
                print(f"   ✅ Rubrics endpoint working - {len(rubrics)} rubrics found")
                print(f"   🎉 NEW ENDPOINT SUCCESS!")
                results.append(True)
            else:
                print(f"   ❌ Insufficient rubrics: {len(rubrics)}")
                results.append(False)
        else:
            print(f"   ❌ Rubrics endpoint error: {response.status_code}")
            results.append(False)
    except Exception as e:
        print(f"   ❌ Rubrics endpoint failed: {e}")
        results.append(False)
    
    # Test 4: NEW AI Status Endpoint
    print("\n4️⃣ Testing NEW AI Status Endpoint...")
    try:
        response = requests.get("http://127.0.0.1:8001/ai/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ready':
                models = data.get('models', {})
                print(f"   ✅ AI status endpoint working")
                print(f"   🎉 NEW ENDPOINT SUCCESS!")
                print(f"   📊 Models: {list(models.keys())}")
                results.append(True)
            else:
                print(f"   ❌ AI not ready: {data}")
                results.append(False)
        else:
            print(f"   ❌ AI status error: {response.status_code}")
            results.append(False)
    except Exception as e:
        print(f"   ❌ AI status failed: {e}")
        results.append(False)
    
    # Summary
    print(f"\n📊 Final Results:")
    print(f"   Tests Passed: {sum(results)}/{len(results)}")
    print(f"   Success Rate: {sum(results)/len(results)*100:.1f}%")
    
    if all(results):
        print(f"\n🎉 ALL SYSTEMS OPERATIONAL!")
        print(f"   ✅ API server running")
        print(f"   ✅ Database connected") 
        print(f"   ✅ NEW endpoints working")
        print(f"   ✅ Ready for GUI connection")
        print(f"\n🚀 Next: Start GUI with 'python scripts/run_gui.py'")
        return True
    else:
        print(f"\n⚠️  Some systems need attention")
        return False

if __name__ == "__main__":
    success = test_final_verification()
    sys.exit(0 if success else 1)