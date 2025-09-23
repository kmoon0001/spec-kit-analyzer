from typing import List

def chunk_text(text: str, max_chars: int = 1000) -> List[str]:
    """
    A simple text chunker that splits text into chunks of a maximum size,
    preferring to split at newlines.
    """
    if not isinstance(text, str) or not text:
        return []

    chunks = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + max_chars, n)

        # Try to find a natural breaking point (newline) in the latter half of the chunk
        newline_pos = text.rfind("\n", start, end)
        if newline_pos != -1 and newline_pos > start + (max_chars // 2):
            end = newline_pos

        chunks.append(text[start:end].strip())
        start = end

    return [chunk for chunk in chunks if chunk]
