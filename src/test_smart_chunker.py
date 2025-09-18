# Python
from __future__ import annotations

import unittest
from .smart_chunker import SmartChunker

class TestSmartChunker(unittest.TestCase):

    def test_simple_split(self):
        """Test that a simple text is split into chunks of the correct size."""
        chunker = SmartChunker(chunk_size=50, chunk_overlap=10)
        text = "This is a test sentence. This is another test sentence. This is a third one to make the text long enough."
        chunks = chunker.split_text(text)
        self.assertTrue(all(len(c) <= 50 for c in chunks))
        self.assertGreater(len(chunks), 1)

    def test_chunk_overlap(self):
        """Test that the overlap between chunks is working correctly."""
        chunker = SmartChunker(chunk_size=30, chunk_overlap=10)
        text = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        chunks = chunker.split_text(text)
        # The first chunk should end with 'd'. The second should start with the overlap from the first.
        # Overlap should be the last 10 chars of the first chunk.
        # A simple check is that the end of the first chunk is in the start of the second.
        self.assertIn(chunks[0][-10:], chunks[1])

    def test_recursive_fallback(self):
        """Test that the chunker uses the prioritized list of separators."""
        # This text has no double newlines, so it should split by single newlines first.
        chunker = SmartChunker(chunk_size=50, chunk_overlap=10)
        text = "First line.\nSecond line, which is a bit longer to test things.\nThird line is shorter."
        chunks = chunker.split_text(text)
        # We expect it to have split by the newline, and merged the first two lines.
        self.assertIn("First line.\nSecond line", chunks[0])
        self.assertIn("Third line", chunks[1])

    def test_no_split_for_short_text(self):
        """Test that text shorter than the chunk size is not split."""
        chunker = SmartChunker(chunk_size=100, chunk_overlap=20)
        text = "This is a short text that should not be split at all."
        chunks = chunker.split_text(text)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], text)

    def test_empty_string(self):
        """Test that an empty string results in an empty list of chunks."""
        chunker = SmartChunker()
        text = ""
        chunks = chunker.split_text(text)
        self.assertEqual(len(chunks), 0)

    def test_respects_paragraphs(self):
        """Test that the chunker prioritizes splitting by paragraphs."""
        chunker = SmartChunker(chunk_size=50, chunk_overlap=10)
        text = "This is the first paragraph.\n\nThis is the second paragraph, which is kept together."
        chunks = chunker.split_text(text)
        self.assertIn("This is the first paragraph.", chunks[0])
        self.assertIn("This is the second paragraph", chunks[1])


if __name__ == '__main__':
    unittest.main()
