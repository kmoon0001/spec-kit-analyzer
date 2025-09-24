def chunk_text(text: str, max_chars: int = 4000):
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

import yaml

def load_config():
    """Loads the application configuration from config.yaml."""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)
