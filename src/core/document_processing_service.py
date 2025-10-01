import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """
    A service to handle multi-format document ingestion (PDF, DOCX, images)
    with validation and text extraction.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._initialize_dependencies()

    def _initialize_dependencies(self):
        """
        Lazy load dependencies to avoid circular imports and improve startup time.
        """
        try:
            from pdf2image import convert_from_path
            import pytesseract
            from docx import Document
            import fitz  # PyMuPDF

            self.convert_from_path = convert_from_path
            self.pytesseract = pytesseract
            self.Document = Document
            self.fitz = fitz
        except ImportError as e:
            logger.error(f"Error importing dependencies: {e}")
            raise

    def process_document(self, file_path: str, file_type: str) -> str:
        """
        Process a document based on its file type and return the extracted text.
        """
        logger.info(f"Processing document: {file_path} ({file_type})")

        if file_type == "pdf":
            return self._process_pdf(file_path)
        elif file_type == "docx":
            return self._process_docx(file_path)
        elif file_type in ["png", "jpg", "jpeg"]:
            return self._process_image(file_path)
        elif file_type == "txt":
            return self._process_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def _process_txt(self, file_path: str) -> str:
        """
        Extract text from a TXT document.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error processing TXT file: {e}")
            raise

    def _process_pdf(self, file_path: str) -> str:
        """
        Extract text from a PDF document.
        """
        try:
            doc = self.fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        except Exception as e:
            logger.error(f"Error processing PDF file: {e}")
            raise

    def _process_docx(self, file_path: str) -> str:
        """
        Extract text from a DOCX document.
        """
        try:
            doc = self.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error processing DOCX file: {e}")
            raise

    def _process_image(self, file_path: str) -> str:
        """
        Extract text from an image file using OCR.
        """
        try:
            images = self.convert_from_path(file_path)
            text = ""
            for image in images:
                text += self.pytesseract.image_to_string(image)
            return text
        except Exception as e:
            logger.error(f"Error processing image file: {e}")
            raise
