# Python
from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the src directory to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Local
from src.guideline_service import GuidelineService
from src.local_llm import LocalRAG


class TestGuidelineService(unittest.TestCase):

    def setUp(self):
        """Set up a mock RAG instance and a GuidelineService instance for testing."""
        # Create a mock for the LocalRAG instance
        self.mock_rag = MagicMock(spec=LocalRAG)
        self.mock_rag.is_ready.return_value = True

        # Instantiate the service with the mock
        self.guideline_service = GuidelineService(self.mock_rag)

        # Create a dummy guideline file for testing
        self.test_guideline_file = "test_guidelines.txt"
        with open(self.test_guideline_file, "w") as f:
            f.write("This is the first guideline paragraph.\n\nThis is the second.")

    def tearDown(self):
        """Clean up the dummy guideline file."""
        if os.path.exists(self.test_guideline_file):
            os.remove(self.test_guideline_file)

    def test_load_and_index_guidelines_local_file(self):
        """Test that loading from a local file correctly calls the indexer."""
        # Arrange
        sources = [self.test_guideline_file]

        # Act
        self.guideline_service.load_and_index_guidelines(sources)

        # Assert
        # Check that create_index was called
        self.mock_rag.create_index.assert_called_once()

        # Check that it was called with the correct text content
        expected_texts = ["This is the first guideline paragraph.", "This is the second."]
        call_args = self.mock_rag.create_index.call_args[0][0]
        self.assertListEqual(call_args, expected_texts)

        self.assertTrue(self.guideline_service.is_index_ready)

    @patch('requests.get')
    def test_load_and_index_guidelines_url(self, mock_get):
        """Test that loading from a URL correctly downloads and calls the indexer."""
        # Arrange
        # Mock the response from requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"dummy pdf content"
        mock_get.return_value = mock_response
        # We need to provide PDF content. We can create a dummy PDF in memory.
        # For simplicity, we will mock the _extract_text_from_pdf call instead.

        sources = ["http://fake-guideline-url.com/guideline.pdf"]

        # We patch the internal text extraction method to avoid dealing with PDF creation
        with patch.object(self.guideline_service, '_extract_text_from_pdf', return_value=[("URL guideline text.", "guideline.pdf (Page 1)")]) as mock_extract:
            # Act
            self.guideline_service.load_and_index_guidelines(sources)

            # Assert
            mock_extract.assert_called_once()
            self.mock_rag.create_index.assert_called_once_with(["URL guideline text."])
            self.assertTrue(self.guideline_service.is_index_ready)

    def test_search_returns_formatted_results(self):
        """Test that the search method calls the RAG search and formats the output."""
        # Arrange
        # First, we need to load some data into the service to enable the index
        self.guideline_service.guideline_chunks = [
            ("This is the first guideline paragraph.", "test_guidelines.txt"),
            ("This is the second.", "test_guidelines.txt")
        ]
        self.guideline_service.is_index_ready = True

        # Configure the mock search_index to return a specific text
        self.mock_rag.search_index.return_value = ["This is the second."]

        # Act
        query = "a query about the second paragraph"
        results = self.guideline_service.search(query, top_k=1)

        # Assert
        self.mock_rag.search_index.assert_called_once_with(query, k=1)

        self.assertEqual(len(results), 1)
        self.assertDictEqual(results[0], {
            "text": "This is the second.",
            "source": "test_guidelines.txt"
        })

if __name__ == '__main__':
    unittest.main()
