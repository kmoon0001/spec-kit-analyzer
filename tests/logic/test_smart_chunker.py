import unittest
from src.text_chunking import RecursiveCharacterTextSplitter

class TestRecursiveCharacterTextSplitter(unittest.TestCase):

    def setUp(self):
        """Set up common variables for tests."""
        self.long_text = "This is the first sentence.\n\nThis is the second sentence. It is a bit longer.\n\nThis is the third sentence, designed to test the chunking functionality of the RecursiveCharacterTextSplitter class. Let's add more words to make it wrap. And a bit more for good measure."
        self.short_text = "This is a short text."

    def test_initialization(self):
        """Test that the chunker initializes with the correct parameters."""
        chunker = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
        self.assertEqual(chunker._chunk_size, 50)
        self.assertEqual(chunker._chunk_overlap, 10)
        self.assertEqual(chunker._separators, ["\n\n", "\n", " ", ""])

    def test_chunking_long_text(self):
        """Test that a long text is split into multiple chunks."""
        chunker = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        chunks = chunker.split_text(self.long_text)
        self.assertTrue(len(chunks) > 1, "The text should be split into multiple chunks")
        for chunk in chunks:
            self.assertTrue(len(chunk) <= 100, f"Chunk is too long: {len(chunk)}")

    def test_chunk_overlap(self):
        """Test that the overlap between chunks is correctly implemented."""
        chunker = RecursiveCharacterTextSplitter(chunk_size=80, chunk_overlap=15)
        text = "This is a sentence that will be used to test the overlap. And this is another part to ensure splitting."
        # Separator is ". "
        # First part: "This is a sentence that will be used to test the overlap." (61 chars)
        # Second part: "And this is another part to ensure splitting." (46 chars)
        # They should be split. Let's make the first part longer.
        text = "This is a very long first sentence that will definitely be used to test the overlap functionality because it needs to be longer than the chunk size."
        # This text is 150 chars.

        chunker = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        chunks = chunker.split_text(text)

        self.assertTrue(len(chunks) > 1)
        # The end of the first chunk should be the start of the second chunk (with overlap)
        overlap_part = chunks[0][-20:]
        self.assertTrue(chunks[1].startswith(overlap_part))

    def test_no_chunking_for_short_text(self):
        """Test that text shorter than chunk_size is not chunked."""
        chunker = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)
        chunks = chunker.split_text(self.short_text)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], self.short_text)

    def test_custom_separators(self):
        """Test chunking with a custom set of separators."""
        text = "Sentence one|Sentence two|Sentence three"
        chunker = RecursiveCharacterTextSplitter(chunk_size=15, chunk_overlap=5, separators=["|"])
        chunks = chunker.split_text(text)
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0], "Sentence one")
        self.assertEqual(chunks[1], "Sentence two")
        self.assertEqual(chunks[2], "Sentence three")

    def test_recursive_splitting(self):
        """Test the recursive nature of the splitting logic."""
        # This text has \n\n, \n, and . separators.
        # The chunker should first split by \n\n.
        # If a resulting chunk is still too large, it should be split by \n, then by .
        text = "Part 1 is here.\nIt has one line break.\n\nPart 2 is here. It is a bit longer to ensure it gets split further. Yes, it really is."
        chunker = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
        chunks = chunker.split_text(text)

        # Expected splits:
        # Initial split by "\n\n":
        # -> "Part 1 is here.\nIt has one line break." (40 chars) -> stays as is
        # -> "Part 2 is here. It is a bit longer to ensure it gets split further. Yes, it really is." (96 chars) -> needs further splitting by ". "
        #    -> "Part 2 is here" (16 chars)
        #    -> "It is a bit longer to ensure it gets split further" (54 chars) -> needs splitting
        #    -> "Yes, it really is." (19 chars)

        self.assertTrue(len(chunks) > 2)
        self.assertIn("Part 1 is here.\nIt has one line break.", chunks)
        # Check that the long second part was split
        self.assertTrue(any("Part 2 is here" in chunk for chunk in chunks))
        self.assertTrue(any("gets split further" in chunk for chunk in chunks))
        self.assertTrue(any("Yes, it really is." in chunk for chunk in chunks))

    def test_empty_text(self):
        """Test that an empty string results in an empty list of chunks."""
        chunker = RecursiveCharacterTextSplitter()
        chunks = chunker.split_text("")
        self.assertEqual(chunks, [])

    def test_text_with_only_separators(self):
        """Test text that consists only of separators."""
        chunker = RecursiveCharacterTextSplitter()
        chunks = chunker.split_text("\n\n\n. \n")
        self.assertEqual(chunks, [])

if __name__ == '__main__':
    unittest.main()
