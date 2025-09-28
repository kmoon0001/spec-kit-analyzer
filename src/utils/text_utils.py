from typing import List


def chunk_text(text: str, max_chars: int = 4000) -> List[str]:
    chunks = []
    start_index = 0
    while start_index < len(text):
        end_index = start_index + max_chars
        if end_index >= len(text):
            chunks.append(text[start_index:])
            break
        split_pos = text.rfind("\n", start_index, end_index)
        if split_pos != -1:
            end_index = split_pos + 1
        chunks.append(text[start_index:end_index])
        start_index = end_index
    return chunks