import unittest
from src.utils import (
    scrub_phi,
    split_sentences,
    _normalize_text,
    _similarity,
    collapse_similar_sentences_simple,
    collapse_similar_sentences_tfidf,
    build_rich_summary,
    count_categories
)

class TestUtils(unittest.TestCase):

    def test_scrub_phi(self):
        text = "Patient phone is 555-123-4567, email is test@example.com, SSN is 000-00-0000. Address: 123 Main St."
        scrubbed = scrub_phi(text)
        self.assertIn("[PHONE]", scrubbed)
        self.assertIn("[EMAIL]", scrubbed)
        self.assertIn("[SSN]", scrubbed)
        self.assertIn("[ADDR]", scrubbed)

    def test_split_sentences(self):
        text = "This is a sentence. This is another one! Is this a third? Yes."
        sentences = split_sentences(text)
        self.assertEqual(len(sentences), 4)
        self.assertEqual(sentences[0], "This is a sentence.")

    def test_normalize_text(self):
        text = "  This IS a  Test.  "
        normalized = _normalize_text(text)
        self.assertEqual(normalized, "this is a test.")

    def test_similarity(self):
        text1 = "This is a test."
        text2 = "This is a test."
        self.assertAlmostEqual(_similarity(text1, text2), 1.0)
        text3 = "This is completely different."
        self.assertLess(_similarity(text1, text3), 0.6)

    def test_collapse_similar_sentences_simple(self):
        items = [("This is a test.", "p1"), ("This is a test.", "p2"), ("A different sentence.", "p3")]
        collapsed = collapse_similar_sentences_simple(items, 0.9)
        self.assertEqual(len(collapsed), 2)

    def test_collapse_similar_sentences_tfidf(self):
        items = [("This is a test.", "p1"), ("This is a test.", "p2"), ("A different sentence.", "p3")]
        collapsed = collapse_similar_sentences_tfidf(items, 0.9)
        self.assertEqual(len(collapsed), 2)

    def test_build_rich_summary(self):
        original = [("This is a test.", "p1"), ("This is another test.", "p2")]
        collapsed = [("This is a test.", "p1")]
        summary = build_rich_summary(original, collapsed)
        self.assertEqual(summary["total_sentences_raw"], 2)
        self.assertEqual(summary["total_sentences_final"], 1)

    def test_count_categories(self):
        issues = [{"category": "A"}, {"category": "B"}, {"category": "A"}]
        counts = count_categories(issues)
        self.assertEqual(counts["A"], 2)
        self.assertEqual(counts["B"], 1)

if __name__ == '__main__':
    unittest.main()
