import os
import yaml
from typing import List

# Get the absolute path to the project's root directory
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def chunk_text(text: str, max_chars: int = 4000) -> List[str]:
    """Splits a text into chunks of a maximum size, attempting to break at newlines."""
    chunks = []
    start_index = 0
    while start_index < len(text):
        end_index = start_index + max_chars

        # If the chunk extends beyond the text, this is the last chunk
        if end_index >= len(text):
            chunks.append(text[start_index:])
            break

        # Otherwise, try to find a newline to split at
        split_pos = text.rfind('\n', start_index, end_index)

        # If a newline is found, split there. Otherwise, split at max_chars.
        if split_pos != -1:
            # The end of the chunk is the character *after* the newline
            end_index = split_pos + 1

        chunks.append(text[start_index:end_index])
        start_index = end_index

    return chunks

def load_config():
    """Loads the application configuration from config.yaml."""
    # Correct the path to point to the project root, not the 'src' directory
    project_root = os.path.dirname(ROOT_DIR)
    config_path = os.path.join(project_root, "config.yaml")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
