#!/usr/bin/env python3
"""
Clean up HuggingFace cache to save disk space after moving models locally.
"""

import os
import shutil
from pathlib import Path

def cleanup_hf_cache():
    """Remove HuggingFace cache to save space."""

    hf_cache = Path.home() / ".cache" / "huggingface" / "hub"

    if not hf_cache.exists():
        print("HuggingFace cache not found.")
        return

    print(f"HuggingFace Cache Location: {hf_cache}")

    # Calculate size before cleanup
    total_size = 0
    for root, dirs, files in os.walk(hf_cache):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                total_size += os.path.getsize(file_path)
            except (OSError, FileNotFoundError):
                pass

    size_gb = total_size / (1024**3)
    print(f"Cache size: {size_gb:.2f} GB")

    # Ask for confirmation
    response = input(f"\nRemove HuggingFace cache ({size_gb:.2f} GB)? (y/N): ").strip().lower()

    if response in ['y', 'yes']:
        try:
            shutil.rmtree(hf_cache)
            print("HuggingFace cache removed successfully!")
            print(f"Freed up {size_gb:.2f} GB of disk space.")
        except Exception as e:
            print(f"Error removing cache: {e}")
    else:
        print("Cache cleanup cancelled.")
        print("\nYou can manually remove the cache later:")
        print(f"  {hf_cache}")

if __name__ == "__main__":
    cleanup_hf_cache()
