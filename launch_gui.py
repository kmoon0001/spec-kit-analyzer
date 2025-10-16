#!/usr/bin/env python3
"""
Simple GUI launcher for the Therapy Compliance Analyzer
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables
os.environ["PYTHONPATH"] = str(project_root)

# Now import and run the GUI
if __name__ == "__main__":
    try:
        from src.gui.main import main
        sys.exit(main())
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you're running from the project root directory")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching GUI: {e}")
        sys.exit(1)