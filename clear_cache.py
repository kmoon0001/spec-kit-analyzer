#!/usr/bin/env python3
"""
Clear all cache files and temporary data that might be causing issues
"""

import os
import shutil
import glob
from pathlib import Path

def clear_cache():
    """Clear all cache files and temporary data"""
    print("🧹 Clearing Cache and Temporary Files")
    print("=" * 40)
    
    cache_dirs = [
        "__pycache__",
        ".pytest_cache", 
        "models/__pycache__",
        "src/__pycache__",
        "src/api/__pycache__",
        "src/core/__pycache__",
        "src/database/__pycache__",
        "src/gui/__pycache__",
        "tests/__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        "temp",
        "tmp",
        "uploads"
    ]
    
    cache_files = [
        "*.pyc",
        "*.pyo", 
        "*.log",
        "*.tmp",
        ".coverage",
        "compliance.db",
        "compliance.db-journal"
    ]
    
    # Clear cache directories
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"   ✅ Removed directory: {cache_dir}")
            except Exception as e:
                print(f"   ⚠️  Could not remove {cache_dir}: {e}")
        else:
            print(f"   ℹ️  Directory not found: {cache_dir}")
    
    # Clear cache files
    for pattern in cache_files:
        files = glob.glob(pattern, recursive=True)
        for file in files:
            try:
                os.remove(file)
                print(f"   ✅ Removed file: {file}")
            except Exception as e:
                print(f"   ⚠️  Could not remove {file}: {e}")
    
    # Clear Python cache recursively
    for root, dirs, files in os.walk("."):
        # Remove __pycache__ directories
        if "__pycache__" in dirs:
            cache_path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(cache_path)
                print(f"   ✅ Removed: {cache_path}")
            except Exception as e:
                print(f"   ⚠️  Could not remove {cache_path}: {e}")
        
        # Remove .pyc files
        for file in files:
            if file.endswith(('.pyc', '.pyo')):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"   ✅ Removed: {file_path}")
                except Exception as e:
                    print(f"   ⚠️  Could not remove {file_path}: {e}")
    
    print(f"\n🎉 Cache clearing complete!")
    print(f"   Now restart the server: python scripts/run_api.py")

if __name__ == "__main__":
    clear_cache()