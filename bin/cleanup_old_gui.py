#!/usr/bin/env python3
"""
Cleanup script to remove old GUI files and migrate to PTside.
Run this after confirming PTside works correctly.
"""

import os
import shutil
from pathlib import Path

# Files to remove (old GUI variants)
OLD_GUI_FILES = [
    "src/gui/main_window_fixed.py",
    "src/gui/main_window_modern.py",
    "src/gui/main_window_working.py",
    "start_app_original_fixed.py",
    "start_app_fixed.py",
    "start_app_simple.py",
    "start_app_minimal.py",
    "start_app_lite.py",
    "start_app_professional.py",
    "start_app_full_professional.py",
    "start_app_full_gui.py",
    "start_app_standalone.py",
    "start_app_enhanced.py",
]

# Optional: Keep main_window.py for reference but rename it
RENAME_FILES = {
    "src/gui/main_window.py": "src/gui/main_window_OLD_BACKUP.py",
    "src/gui/main.py": "src/gui/main_OLD_BACKUP.py",
}

def main():
    print("🧹 PTside Migration Cleanup Script")
    print("=" * 60)
    print()
    
    # Create backup directory
    backup_dir = Path("old_gui_backup")
    if not backup_dir.exists():
        backup_dir.mkdir()
        print(f"✅ Created backup directory: {backup_dir}")
    
    # Move old files to backup
    moved_count = 0
    for file_path in OLD_GUI_FILES:
        if os.path.exists(file_path):
            try:
                dest = backup_dir / Path(file_path).name
                shutil.move(file_path, dest)
                print(f"📦 Moved: {file_path} → {dest}")
                moved_count += 1
            except Exception as e:
                print(f"❌ Error moving {file_path}: {e}")
    
    print()
    print(f"✅ Moved {moved_count} old GUI files to backup")
    print()
    
    # Rename main files for reference
    renamed_count = 0
    for old_name, new_name in RENAME_FILES.items():
        if os.path.exists(old_name):
            try:
                shutil.copy2(old_name, new_name)
                print(f"📝 Backed up: {old_name} → {new_name}")
                renamed_count += 1
            except Exception as e:
                print(f"❌ Error backing up {old_name}: {e}")
    
    print()
    print(f"✅ Created {renamed_count} backup copies")
    print()
    
    # Summary
    print("=" * 60)
    print("🎉 Cleanup Complete!")
    print()
    print("Next steps:")
    print("1. Test PTside: python start_app.py")
    print("2. If everything works, you can delete old_gui_backup/")
    print("3. Update your documentation to reference PTside")
    print()
    print("PTside is now your primary interface! 🏃‍♂️")

if __name__ == "__main__":
    main()
