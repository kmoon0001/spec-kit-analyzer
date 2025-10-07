#!/usr/bin/env python3
"""
Test script to verify router imports are working correctly.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_router_imports():
    """Test that all routers can be imported successfully."""
    print("🔍 Testing Router Imports")
    print("=" * 50)
    
    routers_to_test = [
        ("health", "src.api.routers.health"),
        ("auth", "src.api.routers.auth"),
        ("analysis", "src.api.routers.analysis"),
        ("admin", "src.api.routers.admin"),
        ("dashboard", "src.api.routers.dashboard"),
        ("chat", "src.api.routers.chat"),
        ("compliance", "src.api.routers.compliance"),
        ("habits", "src.api.routers.habits"),
        ("meta_analytics", "src.api.routers.meta_analytics"),
        ("feedback", "src.api.routers.feedback"),
    ]
    
    successful_imports = []
    failed_imports = []
    
    for router_name, module_path in routers_to_test:
        try:
            print(f"\n📦 Testing {router_name} router...")
            module = __import__(module_path, fromlist=['router'])
            
            if hasattr(module, 'router'):
                router = module.router
                print(f"   ✅ {router_name}: Router object found")
                
                # Check if router has routes
                if hasattr(router, 'routes') and router.routes:
                    print(f"   📋 {router_name}: {len(router.routes)} routes found")
                    for route in router.routes[:3]:  # Show first 3 routes
                        if hasattr(route, 'path') and hasattr(route, 'methods'):
                            methods = list(route.methods) if route.methods else ['N/A']
                            print(f"      • {methods[0]} {route.path}")
                else:
                    print(f"   ⚠️ {router_name}: No routes found")
                
                successful_imports.append(router_name)
            else:
                print(f"   ❌ {router_name}: No 'router' attribute found")
                failed_imports.append((router_name, "No router attribute"))
                
        except ImportError as e:
            print(f"   ❌ {router_name}: Import error - {e}")
            failed_imports.append((router_name, f"Import error: {e}"))
        except Exception as e:
            print(f"   ❌ {router_name}: Unexpected error - {e}")
            failed_imports.append((router_name, f"Unexpected error: {e}"))
    
    print("\n" + "=" * 50)
    print(f"✅ Successful imports: {len(successful_imports)}")
    print(f"❌ Failed imports: {len(failed_imports)}")
    
    if failed_imports:
        print("\n🔧 Failed imports details:")
        for router_name, error in failed_imports:
            print(f"   • {router_name}: {error}")
    
    return len(failed_imports) == 0

if __name__ == "__main__":
    success = test_router_imports()
    
    if success:
        print("\n🎉 All routers imported successfully!")
    else:
        print("\n❌ Some routers failed to import!")
        print("Fix the import issues before running the API server.")