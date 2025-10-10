#!/usr/bin/env python3
"""
Final cleanup of remaining syntax errors and logging issues.
"""

import re
from pathlib import Path

def fix_syntax_and_logging_issues(file_path: Path) -> bool:
    """Fix remaining syntax errors and logging issues in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix malformed logging calls with format specifiers
        # Pattern: logger.info("message %s", variable:.1f)
        # Should be: logger.info("message %.1f", variable)
        
        # Fix percentage and float formatting in logging calls
        content = re.sub(r'(\w+):(\.1%)', r'\1 * 100', content)
        content = re.sub(r'(\w+):(\.1f)', r'\1', content)
        content = re.sub(r'(\w+):(\.2f)', r'\1', content)
        content = re.sub(r'(\w+):(\.3f)', r'\1', content)
        
        # Fix format strings with colons in logging calls
        content = re.sub(r'%s%", (\w+):(\.1f)', r'%.1f%%", \1', content)
        content = re.sub(r'%s", (\w+):(\.1f)', r'%.1f", \1', content)
        content = re.sub(r'%s", (\w+):(\.2f)', r'%.2f", \1', content)
        content = re.sub(r'%s", (\w+):(\.3f)', r'%.3f", \1', content)
        content = re.sub(r'%sms", (\w+):(\.1f)', r'%.1fms", \1', content)
        content = re.sub(r'%ss", (\w+):(\.2f)', r'%.2fs", \1', content)
        content = re.sub(r'%sMB", (\w+):(\.1f)', r'%.1fMB", \1', content)
        content = re.sub(r'%s%", (\w+):(\.2f)', r'%.2f%%", \1', content)
        
        # Fix multi-line logging issues
        content = re.sub(r'", (\w+):(\.1f),\s*f"([^"]*)"', r'%.1f\2", \1', content)
        content = re.sub(r'", (\w+):(\.2f),\s*f"([^"]*)"', r'%.2f\2", \1', content)
        content = re.sub(r'", (\w+):(\.1%),\s*f"([^"]*)"', r'%.1f%%\2", \1 * 100', content)
        
        # Fix remaining f-strings in logging calls
        # Pattern: logger.info(f"message {var}")
        # Should be: logger.info("message %s", var)
        
        # Simple f-string with one variable
        pattern = r'(logger\.\w+|logging\.\w+)\(f["\']([^"\']*?)\{([^}]+)\}([^"\']*?)["\']([^)]*)\)'
        
        def replace_fstring(match):
            log_call = match.group(1)
            before_var = match.group(2)
            variable = match.group(3)
            after_var = match.group(4)
            extra_args = match.group(5)
            
            # Create the format string
            message = f'"{before_var}%s{after_var}"'
            
            # Handle extra arguments
            if extra_args.strip():
                if extra_args.strip().startswith(','):
                    return f'{log_call}({message}, {variable}{extra_args})'
                else:
                    return f'{log_call}({message}, {variable}, {extra_args})'
            else:
                return f'{log_call}({message}, {variable})'
        
        content = re.sub(pattern, replace_fstring, content)
        
        # Fix malformed string literals
        content = re.sub(r'f"([^"]*)\{([^}]+)\}([^"]*)"([^,\)])', r'"\1%s\3", \2\4', content)
        
        # Fix broken exception handling syntax
        content = re.sub(r'except\s+([^:]+):\s*as\s+(\w+):', r'except \1 as \2:', content)
        
        # Fix missing quotes in strings
        content = re.sub(r'(["\'])([^"\']*)\{([^}]+)\}([^"\']*)\1', r'\1\2%s\4\1, \3', content)
        
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
    
    print("Final cleanup: fixing remaining syntax errors and logging issues...")
    
    for file_path in python_files:
        if fix_syntax_and_logging_issues(file_path):
            fixed_count += 1
            print(f"Fixed: {file_path}")
    
    print(f"\n✅ Processed {len(python_files)} files, fixed {fixed_count} files.")
    
    # Run a final check
    print("\n🔍 Running final verification...")
    import subprocess
    try:
        result = subprocess.run(['ruff', 'check', 'src/', '--select', 'BLE001,G004'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ All targeted issues have been resolved!")
        else:
            remaining_issues = result.stdout.count('BLE001') + result.stdout.count('G004')
            print(f"⚠️  {remaining_issues} issues still remain")
    except FileNotFoundError:
        print("⚠️  Could not verify with ruff (not installed)")

if __name__ == '__main__':
    main()