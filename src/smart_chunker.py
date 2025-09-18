# Python
from __future__ import annotations

from typing import List

class SmartChunker:
    """
    A text splitter that recursively splits text to create chunks of a specified size,
    with a configurable overlap. It prioritizes splitting on larger semantic units
    (like paragraphs) before falling back to smaller units.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, separators: List[str] | None = None):
        """
        Initializes the SmartChunker.

        Args:
            chunk_size: The target size for each text chunk (in characters).
            chunk_overlap: The number of characters to overlap between chunks.
            separators: A list of separators to split on, in order of priority.
        """
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size.")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]

    def _merge_splits(self, splits: List[str]) -> List[str]:
        """
        Merges small splits together to create chunks closer to the target chunk_size.
        Also handles the overlap between chunks.
        """
        merged_chunks = []
        current_chunk = ""

        for split in splits:
            if len(current_chunk) + len(split) <= self.chunk_size:
                current_chunk += split
            else:
                if current_chunk:
                    merged_chunks.append(current_chunk)
                # Start a new chunk, including overlap from the end of the last one
                overlap = current_chunk[-self.chunk_overlap:] if self.chunk_overlap > 0 else ""
                current_chunk = overlap + split

        if current_chunk:
            merged_chunks.append(current_chunk)

        return merged_chunks

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """
        Recursively splits text based on the provided separators.
        """
        final_chunks = []

        if not text:
            return []

        # If we've run out of separators, we have to split by character
        if not separators:
            for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
                chunk = text[i:i + self.chunk_size]
                final_chunks.append(chunk)
            return final_chunks

        separator = separators[0]
        remaining_separators = separators[1:]

        # Split by the current separator
        splits = text.split(separator)

        for i, split in enumerate(splits):
            if len(split) <= self.chunk_size:
                final_chunks.append(split)
            else:
                # If a split is too large, recurse with the next separator
                final_chunks.extend(self._recursive_split(split, remaining_separators))

            # Re-add the separator, except for the last split
            if i < len(splits) - 1:
                final_chunks.append(separator)

        return final_chunks

    def split_text(self, text: str) -> List[str]:
        """
        The main method to split a large text into chunks using the recursive strategy.

        Args:
            text: The text to be split.

        Returns:
            A list of text chunks.
        """
        if not text:
            return []

        # Perform the initial recursive split
        initial_splits = self._recursive_split(text, self.separators)

        # Merge the small splits into properly sized chunks with overlap
        final_chunks = self._merge_splits(initial_splits)

        return final_chunks
