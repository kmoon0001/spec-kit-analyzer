#!/usr/bin/env python3
"""
Simple script to start the API server for testing.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Start the API server."""
    print("🚀 Starting Therapy Compliance Analyzer API Server...")
    
    # Change to project root
    project_root = Path(__file__).parent
    
    try:
        # Run the API server script
        result = subprocess.run([
            sys.executable, 
            str(project_root / "scripts" / "run_api.py")
        ], cwd=project_root)
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n✅ API server stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())