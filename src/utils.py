import os
import yaml

# Get the absolute path to the project's root directory
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

<<<<<<< HEAD
def chunk_text(text: str, max_chars: int = 4000):
||||||| c46cdd8
def chunk_text(text: str, max_chars: int = 4000) -> List[str]:
    """
    Splits a text into chunks of a maximum size, attempting to break at newlines.
    """
=======
def chunk_text(text: str, max_chars: int = 4000) -> List[str]:
    """Splits a text into chunks of a maximum size, attempting to break at newlines."""
>>>>>>> origin/main
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        newline_pos = text.rfind("\n", start, end)
        if newline_pos != -1 and newline_pos > start + 1000:
            end = newline_pos
        chunks.append(text[start:end])
        start = end
    return chunks

def load_config():
    """Loads the application configuration from config.yaml."""
    config_path = os.path.join(os.path.dirname(ROOT_DIR), "config.yaml")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
