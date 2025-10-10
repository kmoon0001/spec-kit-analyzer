import logging
from typing import Any

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """A service to handle multi-format document ingestion (PDF, DOCX, images)
    with validation and text extraction.
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self._initialize_dependencies()

    def _initialize_dependencies(self):
        """Lazy load dependencies to avoid circular imports and improve startup time."""
        try:
            import fitz  # type: ignore[import-untyped]
            import pytesseract  # type: ignore[import-untyped]
            from docx import Document  # type: ignore[import-untyped]
            from pdf2image import convert_from_path  # type: ignore[import-not-found]

            self.convert_from_path = convert_from_path
            self.pytesseract = pytesseract
            self.Document = Document
            self.fitz = fitz
        except ImportError as e:
            logger.exception("Error importing dependencies: %s", e)
            raise

    def process_document(self, file_path: str, file_type: str) -> str:
        """Process a document based on its file type and return the extracted text."""
        logger.info("Processing document: %s ({file_type})", file_path)

        if file_type == "pdf":
            return self._process_pdf(file_path)
        if file_type == "docx":
            return self._process_docx(file_path)
        if file_type in ["png", "jpg", "jpeg"]:
            return self._process_image(file_path)
        if file_type == "txt":
            return self._process_txt(file_path)
        raise ValueError(f"Unsupported file type: {file_type}")

    def _process_txt(self, file_path: str) -> str:
        """Extract text from a TXT document."""
        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.exception("Error processing TXT file: %s", e)
            raise

    def _process_pdf(self, file_path: str) -> str:
        """Extract text from a PDF document."""
        try:
            doc = self.fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.exception("Error processing PDF file: %s", e)
            raise

    def _process_docx(self, file_path: str) -> str:
        """Extract text from a DOCX document."""
        try:
            doc = self.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.exception("Error processing DOCX file: %s", e)
            raise

    def _process_image(self, file_path: str) -> str:
        """Extract text from an image file using OCR."""
        try:
            images = self.convert_from_path(file_path)
            text = ""
            for image in images:
                text += self.pytesseract.image_to_string(image)
            return text
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.exception("Error processing image file: %s", e)
            raise
