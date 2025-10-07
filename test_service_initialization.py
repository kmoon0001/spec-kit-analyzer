#!/usr/bin/env python3
"""
Test script to check if services are being initialized properly.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_service_initialization():
    """Test service initialization directly."""
    print("🔧 Testing Service Initialization")
    print("=" * 50)
    
    try:
        # Test 1: Check if we can import and create AnalysisService
        print("\n1️⃣ Testing AnalysisService import and creation...")
        
        from src.core.analysis_service import AnalysisService
        from src.core.hybrid_retriever import HybridRetriever
        
        print("   ✅ Imports successful")
        
        # Test 2: Create retriever
        print("\n2️⃣ Creating HybridRetriever...")
        retriever = HybridRetriever()
        print("   ✅ HybridRetriever created")
        
        # Test 3: Initialize retriever
        print("\n3️⃣ Initializing retriever...")
        import asyncio
        asyncio.run(retriever.initialize())
        print("   ✅ HybridRetriever initialized")
        
        # Test 4: Create AnalysisService
        print("\n4️⃣ Creating AnalysisService...")
        analysis_service = AnalysisService(retriever=retriever)
        print("   ✅ AnalysisService created successfully")
        
        # Test 5: Check if service has required attributes
        print("\n5️⃣ Checking service attributes...")
        required_attrs = ['phi_scrubber', 'preprocessing_service', 'compliance_analyzer']
        
        for attr in required_attrs:
            if hasattr(analysis_service, attr):
                print(f"   ✅ {attr}: Present")
            else:
                print(f"   ❌ {attr}: Missing")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error during service initialization: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dependency_injection():
    """Test the dependency injection system."""
    print("\n" + "=" * 50)
    print("🔗 Testing Dependency Injection")
    print("=" * 50)
    
    try:
        from src.api.dependencies import startup_event, get_analysis_service, app_state
        
        print("\n1️⃣ Testing startup event...")
        import asyncio
        asyncio.run(startup_event())
        print("   ✅ Startup event completed")
        
        print("\n2️⃣ Checking app_state...")
        print(f"   App state keys: {list(app_state.keys())}")
        
        if "analysis_service" in app_state:
            service = app_state["analysis_service"]
            print(f"   ✅ analysis_service found: {type(service)}")
        else:
            print("   ❌ analysis_service not found in app_state")
            return False
        
        print("\n3️⃣ Testing get_analysis_service()...")
        service = get_analysis_service()
        if service is not None:
            print(f"   ✅ get_analysis_service() returned: {type(service)}")
            return True
        else:
            print("   ❌ get_analysis_service() returned None")
            return False
            
    except Exception as e:
        print(f"   ❌ Error in dependency injection test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🏥 Therapy Compliance Analyzer - Service Initialization Test")
    print()
    
    # Test direct service creation
    service_success = test_service_initialization()
    
    # Test dependency injection
    di_success = test_dependency_injection()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Service Creation: {'✅ PASS' if service_success else '❌ FAIL'}")
    print(f"   Dependency Injection: {'✅ PASS' if di_success else '❌ FAIL'}")
    
    if service_success and di_success:
        print("\n🎉 All service initialization tests PASSED!")
        print("The analysis service should be working correctly.")
    else:
        print("\n❌ Service initialization tests FAILED!")
        print("Fix the issues above before running the analysis workflow.")