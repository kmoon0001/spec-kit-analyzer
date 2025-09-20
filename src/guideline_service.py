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
from .local_llm import LocalRAG

logger = logging.getLogger(__name__)


class GuidelineService:
    """
    Manages loading, indexing, and searching of compliance guidelines.
    """

    def __init__(self, rag_instance: LocalRAG):
        """
        Initializes the GuidelineService.

        Args:
            rag_instance: An instance of the LocalRAG service for semantic indexing.
        """
        self.rag = rag_instance
        self.guideline_chunks: List[Tuple[str, str]] = []
        self.is_index_ready = False

    def load_and_index_guidelines(self, sources: List[str]) -> None:
        """
        Loads guidelines from a list of sources (URLs or local paths) and builds the search index.

        Args:
            sources: A list of strings, where each string is a URL to a PDF or a local file path.
        """
        logger.info(f"Loading guidelines from {len(sources)} sources...")
        all_chunks = []
        for source in sources:
            try:
                if source.startswith(('http://', 'https://')):
                    chunks = self._load_from_url(source)
                else:
                    chunks = self._load_from_local_path(source)

                if chunks:
                    all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Failed to load or process guideline source '{source}': {e}")

        self.guideline_chunks = all_chunks

        if self.guideline_chunks:
            logger.info(f"Creating search index from {len(self.guideline_chunks)} text chunks...")
            # The RAG instance is responsible for creating the index.
# We pass only the text content for embedding.
            texts_to_index = [chunk[0] for chunk in self.guideline_chunks]
            self.rag.create_index(texts_to_index)
            self.is_index_ready = True
            logger.info("Guideline index is ready.")
        else:
            logger.warning("No guideline text was extracted. Index was not built.")
            self.is_index_ready = False

    def _extract_text_from_pdf(self, file_path: str, source_name: str) -> List[Tuple[str, str]]:
        """Extracts text from a PDF file, chunking it by paragraph."""
        chunks = []
        try:
            # For .txt files, just read the lines
            if file_path.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                paragraphs = text.split('\n\n')
                for para in paragraphs:
                    cleaned_para = para.replace('\n', ' ').strip()
                    if cleaned_para:
                        chunks.append((cleaned_para, source_name))
                return chunks

            # For PDF files
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        paragraphs = text.split('\n\n')
                        for para in paragraphs:
                            cleaned_para = para.replace('\n', ' ').strip()
                            if cleaned_para:
                                chunks.append((cleaned_para, f"{source_name} (Page {i+1})"))
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
        Searches the guideline index for text relevant to the query.

        Args:
            query: The text to search for (e.g., a compliance issue description).
            top_k: The number of top results to return.

        Returns:
            A list of dictionaries, where each dictionary contains the 'text' and 'source' of the guideline.
        """
        if not self.is_index_ready:
            logger.warning("Search attempted before guideline index was ready.")
            return []

        # Use the new search_index method from LocalRAG
        retrieved_texts = self.rag.search_index(query, k=top_k)

        # The retrieved_texts are just the text content. We need to find the original source.
        # We can do this by creating a lookup map from text to source.
        text_to_source_map = {text: source for text, source in self.guideline_chunks}

        results = []
        for text in retrieved_texts:
            source = text_to_source_map.get(text, "Unknown Source")
            results.append({"text": text, "source": source})

        return results
