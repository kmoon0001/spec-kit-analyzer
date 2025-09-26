import sys
import os

# Add the project root directory to the Python path to allow for absolute imports
# of modules in `src`. This makes `from src.main import ...` work correctly
# in the test files located in the `tests/` directory.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

import logging

def pytest_configure(config):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')