import unittest
from unittest.mock import patch, MagicMock
import os
from src.core.document_processing_service import DocumentProcessingService

class TestDocumentProcessingService(unittest.TestCase):

    def setUp(self):
        self.config = {}
        # Create a dummy file for testing
        self.test_txt_file = "test_document.txt"
        with open(self.test_txt_file, "w") as f:
            f.write("This is a test text file.")

        # Patch the method that initializes the dependencies to prevent real imports
        self.init_patch = patch.object(DocumentProcessingService, '_initialize_dependencies', autospec=True)
        self.mock_init_deps = self.init_patch.start()

        # Now, instantiate the service. The real _initialize_dependencies won't be called.
        self.doc_service = DocumentProcessingService(self.config)

        # Manually set the mocked dependencies on the instance
        self.doc_service.fitz = MagicMock()
        self.doc_service.Document = MagicMock()
        self.doc_service.pytesseract = MagicMock()
        self.doc_service.convert_from_path = MagicMock()

    def tearDown(self):
        os.remove(self.test_txt_file)
        self.init_patch.stop()

    def test_process_txt_file(self):
        """Test processing a .txt file"""
        content = self.doc_service.process_document(self.test_txt_file, "txt")
        self.assertEqual(content, "This is a test text file.")

    def test_unsupported_file_type(self):
        """Test that an unsupported file type raises a ValueError"""
        with self.assertRaises(ValueError):
            self.doc_service.process_document("test.unsupported", "unsupported")

if __name__ == '__main__':
    unittest.main()