#!/usr/bin/env python3
"""Convert PyQt6 imports to PySide6 imports."""

import re
from pathlib import Path

def convert_file(file_path):
    """Convert PyQt6 imports to PySide6 in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Convert imports
        content = re.sub(r'from PyQt6\.', 'from PySide6.', content)
        content = re.sub(r'import PyQt6\.', 'import PySide6.', content)
        
        # Convert signal names
        content = re.sub(r'pyqtSignal', 'Signal', content)
        
        # Only write if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Converted: {file_path}")
            return True
        return False
        
    except Exception as e:
        print(f"✗ Error converting {file_path}: {e}")
        return False

def main():
    """Convert all Python files in src/gui/ from PyQt6 to PySide6."""
    gui_dir = Path("src/gui")
    converted_count = 0
    
    if not gui_dir.exists():
        print("src/gui directory not found!")
        return
    
    # Find all Python files
    python_files = list(gui_dir.rglob("*.py"))
    
    print(f"Found {len(python_files)} Python files in src/gui/")
    print("Converting PyQt6 imports to PySide6...")
    
    for file_path in python_files:
        if convert_file(file_path):
            converted_count += 1
    
    print(f"\n✅ Conversion complete! {converted_count} files converted.")
    
    # Also convert run_gui.py
    if Path("run_gui.py").exists():
        if convert_file("run_gui.py"):
            print("✓ Also converted run_gui.py")

if __name__ == "__main__":
    main()