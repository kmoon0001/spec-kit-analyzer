#!/usr/bin/env python3
"""
Analysis of missing endpoints based on 404 errors from the logs
"""

missing_endpoints = [
    {
        "path": "/rubrics",
        "method": "GET",
        "purpose": "Get available compliance rubrics",
        "router": "compliance.py",
        "priority": "HIGH"
    },
    {
        "path": "/analysis/submit", 
        "method": "POST",
        "purpose": "Submit document for analysis",
        "router": "analysis.py", 
        "priority": "HIGH"
    },
    {
        "path": "/tasks/{task_id}",
        "method": "GET", 
        "purpose": "Check analysis task status",
        "router": "analysis.py",
        "priority": "HIGH"
    },
    {
        "path": "/ai/status",
        "method": "GET",
        "purpose": "Check AI model status", 
        "router": "health.py or analysis.py",
        "priority": "MEDIUM"
    },
    {
        "path": "/auth/token",
        "method": "POST",
        "purpose": "User authentication - EXISTS but may have routing issue",
        "router": "auth.py",
        "priority": "HIGH"
    }
]

def analyze_missing_endpoints():
    print("🔍 Missing Endpoints Analysis")
    print("=" * 50)
    
    for endpoint in missing_endpoints:
        print(f"\n📍 {endpoint['method']} {endpoint['path']}")
        print(f"   Purpose: {endpoint['purpose']}")
        print(f"   Router: {endpoint['router']}")
        print(f"   Priority: {endpoint['priority']}")
    
    print(f"\n📊 Summary:")
    print(f"   Total missing: {len(missing_endpoints)}")
    print(f"   High priority: {len([e for e in missing_endpoints if e['priority'] == 'HIGH'])}")
    print(f"   Medium priority: {len([e for e in missing_endpoints if e['priority'] == 'MEDIUM'])}")

if __name__ == "__main__":
    analyze_missing_endpoints()