#!/usr/bin/env python3
"""
Document chunking service for handling large PDFs and text documents.
Implements token-aware chunking for transformer models.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DocumentChunker:
    """Service for chunking large documents into manageable pieces."""

    def __init__(self, max_tokens: int = 512, overlap_tokens: int = 50):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.sentence_endings = r"[.!?]+"
        self.paragraph_breaks = r"\n\s*\n"

    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Chunk text into overlapping segments suitable for processing.

        Args:
            text: The text to chunk

        Returns:
            List of chunks with metadata
        """
        if not text or len(text.strip()) == 0:
            return []

        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        estimated_tokens = len(text) // 4

        if estimated_tokens <= self.max_tokens:
            return [
                {
                    "text": text.strip(),
                    "chunk_index": 0,
                    "total_chunks": 1,
                    "estimated_tokens": estimated_tokens,
                    "start_char": 0,
                    "end_char": len(text),
                }
            ]

        # Split into sentences first
        sentences = self._split_into_sentences(text)

        # Group sentences into chunks
        chunks = self._group_sentences_into_chunks(sentences)

        return chunks

    def _split_into_sentences(self, text: str) -> List[Dict[str, Any]]:
        """Split text into sentences with metadata."""
        sentences = []
        sentence_pattern = r"[.!?]+"

        # Find sentence boundaries
        matches = list(re.finditer(sentence_pattern, text))

        if not matches:
            # No sentence endings found, treat as single sentence
            return [
                {
                    "text": text.strip(),
                    "start_char": 0,
                    "end_char": len(text),
                    "estimated_tokens": len(text) // 4,
                }
            ]

        # Extract sentences
        last_end = 0
        for i, match in enumerate(matches):
            sentence_text = text[last_end : match.end()].strip()
            if sentence_text:
                sentences.append(
                    {
                        "text": sentence_text,
                        "start_char": last_end,
                        "end_char": match.end(),
                        "estimated_tokens": len(sentence_text) // 4,
                    }
                )
            last_end = match.end()

        # Handle remaining text
        if last_end < len(text):
            remaining_text = text[last_end:].strip()
            if remaining_text:
                sentences.append(
                    {
                        "text": remaining_text,
                        "start_char": last_end,
                        "end_char": len(text),
                        "estimated_tokens": len(remaining_text) // 4,
                    }
                )

        return sentences

    def _group_sentences_into_chunks(
        self, sentences: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Group sentences into chunks respecting token limits."""
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_tokens = sentence["estimated_tokens"]

            # If adding this sentence would exceed the limit, start a new chunk
            if current_tokens + sentence_tokens > self.max_tokens and current_chunk:
                # Create chunk from current sentences
                chunk_text = " ".join(s["text"] for s in current_chunk)
                chunks.append(
                    {
                        "text": chunk_text,
                        "chunk_index": chunk_index,
                        "total_chunks": 0,  # Will be updated later
                        "estimated_tokens": current_tokens,
                        "start_char": current_chunk[0]["start_char"],
                        "end_char": current_chunk[-1]["end_char"],
                        "sentences": current_chunk.copy(),
                    }
                )

                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(current_chunk)
                current_chunk = overlap_sentences + [sentence]
                current_tokens = sum(s["estimated_tokens"] for s in current_chunk)
                chunk_index += 1
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens

        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(s["text"] for s in current_chunk)
            chunks.append(
                {
                    "text": chunk_text,
                    "chunk_index": chunk_index,
                    "total_chunks": 0,  # Will be updated
                    "estimated_tokens": current_tokens,
                    "start_char": current_chunk[0]["start_char"],
                    "end_char": current_chunk[-1]["end_char"],
                    "sentences": current_chunk.copy(),
                }
            )

        # Update total_chunks count
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk["total_chunks"] = total_chunks

        return chunks

    def _get_overlap_sentences(
        self, sentences: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get sentences for overlap between chunks."""
        if len(sentences) <= 1:
            return []

        # Take last few sentences for overlap
        overlap_count = min(2, len(sentences) // 2)
        return sentences[-overlap_count:]

    def chunk_document_by_sections(
        self, text: str, section_headers: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk document by sections (useful for clinical documents).

        Args:
            text: The document text
            section_headers: List of section headers to split on

        Returns:
            List of section chunks
        """
        if not section_headers:
            section_headers = [
                "Subjective",
                "Objective",
                "Assessment",
                "Plan",
                "Chief Complaint",
                "History of Present Illness",
                "Review of Systems",
                "Physical Examination",
                "Diagnosis",
                "Treatment",
                "Follow-up",
            ]

        sections = self._split_by_sections(text, section_headers)
        chunks = []

        for section in sections:
            section_chunks = self.chunk_text(section["text"])
            for chunk in section_chunks:
                chunk["section"] = section["header"]
                chunk["section_index"] = section["index"]
            chunks.extend(section_chunks)

        return chunks

    def _split_by_sections(self, text: str, headers: List[str]) -> List[Dict[str, Any]]:
        """Split text by section headers."""
        sections = []

        # Create regex pattern for headers
        header_pattern = (
            r"^\s*(" + "|".join(re.escape(h) for h in headers) + r")\s*:?\s*"
        )

        # Find all header matches
        matches = list(re.finditer(header_pattern, text, re.IGNORECASE | re.MULTILINE))

        if not matches:
            # No sections found, treat as single section
            return [
                {
                    "header": "Full Document",
                    "text": text,
                    "index": 0,
                    "start_char": 0,
                    "end_char": len(text),
                }
            ]

        # Extract sections
        for i, match in enumerate(matches):
            header = match.group(1)
            start_pos = match.start()

            # Find end position (start of next section or end of text)
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)

            section_text = text[start_pos:end_pos].strip()
            sections.append(
                {
                    "header": header,
                    "text": section_text,
                    "index": i,
                    "start_char": start_pos,
                    "end_char": end_pos,
                }
            )

        return sections


# Global chunker instance
_chunker: Optional[DocumentChunker] = None


def get_document_chunker() -> DocumentChunker:
    """Get the global document chunker instance."""
    global _chunker
    if _chunker is None:
        _chunker = DocumentChunker()
    return _chunker


def chunk_text(text: str, max_tokens: int = 512) -> List[Dict[str, Any]]:
    """Convenience function to chunk text."""
    chunker = DocumentChunker(max_tokens=max_tokens)
    return chunker.chunk_text(text)
