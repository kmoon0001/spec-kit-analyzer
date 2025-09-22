# Python
from __future__ import annotations

# Standard library
import logging
import os
import tempfile
from typing import List, Tuple

# Third-party
import pdfplumber
import requests

# Local
# from .local_llm import LocalRAG

logger = logging.getLogger(__name__)


class GuidelineService:
    """
    Manages loading, indexing, and searching of compliance guidelines.
    This is a placeholder implementation.
    """

    def __init__(self, rag_instance = None):
        """
        Initializes the GuidelineService.
        """
        self.rag = rag_instance
        self.guideline_chunks: List[Tuple[str, str]] = []
        self.is_index_ready = False
        logger.info("GuidelineService initialized with placeholder implementation. No indexing will occur.")

    def load_and_index_guidelines(self, sources: List[str]) -> None:
        """
        Placeholder for loading guidelines. Does not index.
        """
        logger.info(f"GuidelineService.load_and_index_guidelines called, but service is a placeholder. Guidelines will not be indexed.")
        self.is_index_ready = False

    def _extract_text_from_pdf(
        self, file_path: str, source_name: str
    ) -> List[Tuple[str, str]]:
        """Extracts text from a PDF file, chunking it by paragraph."""
        chunks = []
        try:
            if file_path.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                paragraphs = text.split('\n\n')
                for para in paragraphs:
                    cleaned_para = para.replace('\n', ' ').strip()
                    if cleaned_para:
                        chunks.append((cleaned_para, source_name))
                return chunks

            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        paragraphs = text.split('\n\n')
                        for para in paragraphs:
                            cleaned_para = para.replace('\n', ' ').strip()
                            if cleaned_para:
                                chunks.append(
                                    (cleaned_para, f"{source_name} (Page {i+1})")
                                )
        except Exception as e:
            logger.error(f"Failed to extract text from '{file_path}': {e}")
            raise
        return chunks

    def _load_from_url(self, url: str) -> List[Tuple[str, str]]:
        """Downloads a PDF from a URL, extracts text, and cleans up."""
        logger.info(f"Downloading and parsing guidelines from {url}...")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                tmp_file.write(response.content)
                tmp_file_path = tmp_file.name
            except requests.RequestException as e:
                logger.error(f"Failed to download PDF from {url}: {e}")
                os.unlink(tmp_file.name)
                return []

        try:
            source_name = os.path.basename(url)
            return self._extract_text_from_pdf(tmp_file_path, source_name)
        finally:
            os.unlink(tmp_file_path)

    def _load_from_local_path(self, file_path: str) -> List[Tuple[str, str]]:
        """Loads and extracts text chunks from a local file."""
        logger.info(f"Parsing guidelines from local file: {file_path}...")
        if not os.path.exists(file_path):
            logger.error(f"Local guideline file not found: {file_path}")
            return []

        source_name = os.path.basename(file_path)
        return self._extract_text_from_pdf(file_path, source_name)

    def search(self, query: str, top_k: int = 2) -> List[dict]:
        """
        Placeholder for searching the guideline index. Returns an empty list.
        """
        logger.warning("GuidelineService.search called, but service is a placeholder. Returning empty list.")
        return []
