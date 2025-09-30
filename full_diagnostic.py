import os
import importlib
import sys
import traceback

def find_python_files(root_dir):
    """Finds all Python files in a directory, ignoring __pycache__."""
    py_files = []
    for root, dirs, files in os.walk(root_dir):
        # Exclude __pycache__ directories from the search
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')

        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
    return py_files

def path_to_module(file_path):
    """Converts a file path to a Python module path."""
    # Remove the '.py' extension
    module_path = file_path[:-3]
    # Replace path separators with dots
    module_path = module_path.replace(os.path.sep, '.')
    return module_path

def main():
    """
    Systematically imports all modules in the 'src' directory to find the first
    one that causes an import error.
    """
    print("--- Starting Full Diagnostic Import Check ---")
    src_dir = "src"

    # Add the current directory to the Python path to allow imports from 'src'
    sys.path.insert(0, os.path.abspath("."))

    py_files = find_python_files(src_dir)

    if not py_files:
        print("Error: No Python files found in the 'src' directory.")
        return

    all_imports_succeeded = True
    # Sort the files to ensure a consistent import order for reproducibility
    for file_path in sorted(py_files):
        module_name = path_to_module(file_path)

        # Skip empty __init__.py files, as they are not meant to be imported directly
        if file_path.endswith("__init__.py") and os.path.getsize(file_path) == 0:
            continue

        print(f"[*] Checking: {module_name}")
        try:
            # The core of the diagnostic: try to import the module
            importlib.import_module(module_name)
        except Exception as e:
            print("\n" + "="*60)
            print("!!! IMPORT ERROR DETECTED !!!")
            print(f"Failed to import module: {module_name}")
            print("="*60)
            print("Traceback:")
            traceback.print_exc()
            print("="*60)
            print("This is the root cause of the server crash.")
            print("Please fix the import error in the file above and re-run this diagnostic script.")
            all_imports_succeeded = False
            # Stop after the first error to provide a clear, actionable target
            break

    if all_imports_succeeded:
        print("\n--- Full Diagnostic Check Complete ---")
        print("All modules imported successfully. The application should be able to start.")
    else:
        print("\n--- Diagnostic Check Failed ---")

if __name__ == "__main__":
    main()