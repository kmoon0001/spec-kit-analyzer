#!/usr/bin/env python3
"""
Fix Exception Handling Script

Automatically fixes B904 exception handling issues by adding proper exception chaining.
"""

import re
import sys
from pathlib import Path

def fix_exception_handling(file_path: Path) -> bool:
    """Fix exception handling in a single file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Pattern 1: raise HTTPException(...) -> raise HTTPException(...) from e
        pattern1 = r'(\s+)raise HTTPException\((.*?)\)(\s*#.*)?$'
        
        lines = content.split('\n')
        modified = False
        
        for i, line in enumerate(lines):
            # Look for raise HTTPException patterns
            if 'raise HTTPException(' in line and ' from ' not in line:
                # Check if we're in an except block by looking backwards
                in_except_block = False
                exception_var = None
                
                for j in range(i-1, max(0, i-10), -1):
                    prev_line = lines[j].strip()
                    if prev_line.startswith('except '):
                        in_except_block = True
                        # Extract exception variable name
                        if ' as ' in prev_line:
                            exception_var = prev_line.split(' as ')[-1].rstrip(':').strip()
                        break
                    elif prev_line.startswith(('def ', 'class ', 'if ', 'elif ', 'else:', 'try:')):
                        break
                
                if in_except_block:
                    # Add 'from e' or 'from None' to the raise statement
                    if exception_var and exception_var != 'Exception':
                        if not line.rstrip().endswith(f' from {exception_var}'):
                            lines[i] = line.rstrip() + f' from {exception_var}'
                            modified = True
                    else:
                        if not line.rstrip().endswith(' from None'):
                            lines[i] = line.rstrip() + ' from None'
                            modified = True
        
        if modified:
            new_content = '\n'.join(lines)
            file_path.write_text(new_content, encoding='utf-8')
            print(f"✅ Fixed exception handling in {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Fix exception handling in all source files."""
    print("🔧 Fixing Exception Handling Issues (B904)")
    print("=" * 50)
    
    src_dir = Path("src")
    if not src_dir.exists():
        print("❌ src/ directory not found")
        return False
    
    # Find all Python files
    python_files = list(src_dir.rglob("*.py"))
    
    fixed_count = 0
    total_count = len(python_files)
    
    for file_path in python_files:
        if fix_exception_handling(file_path):
            fixed_count += 1
    
    print(f"\n📊 Results: Fixed {fixed_count}/{total_count} files")
    
    # Verify the fixes worked
    print("\n🔍 Verifying fixes...")
    import subprocess
    result = subprocess.run(
        ["python", "-m", "ruff", "check", "src/", "--select=B904", "--statistics"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ All B904 issues fixed!")
        return True
    else:
        remaining = result.stdout.count("B904")
        print(f"⚠️ {remaining} B904 issues remaining")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)