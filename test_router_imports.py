_pycache__
   ✅ Removed: .\.venv\pydevd_attach_to_process\winappdbg\win32\__pycache__
   ✅ Removed: .\.venv\Scripts\__pycache__
   ✅ Removed: .\bin\__pycache__
   ✅ Removed: .\scripts\__pycache__
   ✅ Removed: .\src\api\routers\__pycache__
   ✅ Removed: .\src\gui\components\__pycache__
   ✅ Removed: .\src\gui\dialogs\__pycache__
   ✅ Removed: .\src\gui\widgets\__pycache__
   ✅ Removed: .\src\gui\workers\__pycache__
   ✅ Removed: .\src\ml\__pycache__
   ✅ Removed: .\src\utils\__pycache__
   ✅ Removed: .\tests\gui\__pycache__
   ✅ Removed: .\tests\integration\__pycache__
   ✅ Removed: .\tests\logic\__pycache__
   ✅ Removed: .\tests\regression\__pycache__
   ✅ Removed: .\tests\unit\__pycache__
   ✅ Removed: .\tests\_stability\__pycache__

🎉 Cache clearing complete!
   Now restart the server: python scripts/run_api.py
PS C:\Users\kevin\PycharmProjects\Letsgo#999> python check_server_direct.py
🔍 Direct Server Check
==============================
Testing basic connection...
❌ Connection Error: HTTPConnectionPool(host='127.0.0.1', port=8001): Max retries exceeded with url: / (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x00000243A62602F0>: Failed to establish a new connection: [WinError 10061] No connection could be made because the target machine actively refused it'))
   Server may not be running or on different port
PS C:\Users\kevin\PycharmProjects\Letsgo#999> ^C
PS C:\Users\kevin\PycharmProjects\Letsgo#999> ^C
PS C:\Users\kevin\PycharmProjects\Letsgo#999> 
PS C:\Users\kevin\PycharmProjects\Letsgo#999> ^C
PS C:\Users\kevin\PycharmProjects\Letsgo#999> python wait_for_server.py    
⏳ Waiting for API server to start...
   (Restart server with: python scripts/run_api.py)
==================================================
🔍 Attempt 6/60: Testing connection...Traceback (most recent call last):
  File "C:\Users\kevin\PycharmProjects\Letsgo#999\wait_for_server.py", line 74, in <module>
    success = wait_for_server()
  File "C:\Users\kevin\PycharmProjects\Letsgo#999\wait_for_server.py", line 66, in wait_for_server
    time.sleep(5)  # Wait 5 seconds between attempts
    ~~~~~~~~~~^^^
KeyboardInterrupt
PS C:\Users\kevin\Pycha
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