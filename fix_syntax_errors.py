#!/usr/bin/env python3
"""
Fix remaining syntax errors from logging fixes.
"""

import re
from pathlib import Path

def fix_syntax_errors_in_file(file_path: Path) -> bool:
    """Fix syntax errors in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix malformed logging calls with format specifiers
        # Pattern: logger.info("message %s", variable:.1f)
        # Should be: logger.info("message %.1f", variable)
        
        # Fix percentage formatting
        content = re.sub(r'(\w+):(\.1%)', r'\1 * 100', content)
        content = re.sub(r'(\w+):(\.1f)', r'\1', content)
        content = re.sub(r'(\w+):(\.2f)', r'\1', content)
        
        # Fix format strings with colons
        content = re.sub(r'%s%", (\w+):(\.1f)', r'%.1f%%", \1', content)
        content = re.sub(r'%s", (\w+):(\.1f)', r'%.1f", \1', content)
        content = re.sub(r'%s", (\w+):(\.2f)', r'%.2f", \1', content)
        content = re.sub(r'%sms", (\w+):(\.1f)', r'%.1fms", \1', content)
        content = re.sub(r'%ss", (\w+):(\.2f)', r'%.2fs", \1', content)
        content = re.sub(r'%sMB", (\w+):(\.1f)', r'%.1fMB", \1', content)
        
        # Fix multi-line logging issues
        content = re.sub(r'", (\w+):(\.1f),\s*f"([^"]*)"', r'%.1f\2", \1', content)
        content = re.sub(r'", (\w+):(\.2f),\s*f"([^"]*)"', r'%.2f\2", \1', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function."""
    src_dir = Path('src')
    python_files = list(src_dir.rglob('*.py'))
    fixed_count = 0
    
    print("Fixing syntax errors from logging fixes...")
    
    for file_path in python_files:
        if fix_syntax_errors_in_file(file_path):
            fixed_count += 1
            print(f"Fixed: {file_path}")
    
    print(f"\n✅ Processed {len(python_files)} files, fixed {fixed_count} files.")

if __name__ == '__main__':
    main()