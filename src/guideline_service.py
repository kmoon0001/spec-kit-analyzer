# Python
from __future__ import annotations

# Standard library
import json
import logging
import os
import pickle
from typing import List, Tuple

# Third-party
import pdfplumber
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from src.utils import load_config

logger = logging.getLogger(__name__)


class GuidelineService:
    """
    Manages loading, indexing, and searching of compliance guidelines using a neural retriever.
    Implements caching for the FAISS index and guideline chunks to improve startup time.
    """

    def __init__(self, sources: List[str]):
        """Initializes the GuidelineService."""
        self.config = load_config()
        model_name = self.config["models"]["retriever"]

        self.guideline_chunks: List[Tuple[str, str]] = []
        self.is_index_ready = False
        self.faiss_index = None

        self.cache_dir = "data"
        self.index_path = os.path.join(self.cache_dir, "guidelines.index")
        self.chunks_path = os.path.join(self.cache_dir, "guidelines.pkl")
        self.source_paths = sources

        logger.info(f"Loading Sentence Transformer model: {model_name}")
        self.model = SentenceTransformer(model_name)

        self._load_or_build_index()
        logger.info("GuidelineService initialized.")

    @staticmethod
    def classify_document(document_text: str) -> str:
        """
        Classifies the document based on its content.
        Placeholder implementation.
        """
        return "Unknown"

    def _load_or_build_index(self):
        """Loads the index from cache if valid, otherwise builds it from source."""
        if self._is_cache_valid():
            logger.info("Loading guidelines index from cache...")
            self._load_index_from_cache()
        else:
            logger.info("Cache not found or is invalid. Building index from source...")
            self._build_index_from_sources()
            self._save_index_to_cache()

    def _is_cache_valid(self) -> bool:
        """Checks if the cached index and chunks exist and are up-to-date."""
        if not os.path.exists(self.index_path) or not os.path.exists(self.chunks_path):
            return False

        # Check if the sources have changed
        with open(self.chunks_path, "rb") as f:
            cached_chunks = pickle.load(f)
        cached_sources = {chunk[1] for chunk in cached_chunks}
        current_sources = {os.path.basename(path) for path in self.source_paths}
        if cached_sources != current_sources:
            return False

        cache_mod_time = os.path.getmtime(self.index_path)
        for src_path in self.source_paths:
            if (
                not os.path.exists(src_path)
                or os.path.getmtime(src_path) > cache_mod_time
            ):
                return False  # Source file is newer than cache
        return True

    def _load_index_from_cache(self):
        """Loads the FAISS index and guideline chunks from disk."""
        try:
            self.faiss_index = faiss.read_index(self.index_path)
            with open(self.chunks_path, "rb") as f:
                self.guideline_chunks = pickle.load(f)
            self.is_index_ready = True
            logger.info(
                f"Successfully loaded {len(self.guideline_chunks)} chunks and FAISS index from cache."
            )
        except Exception as e:
            logger.error(f"Failed to load index from cache: {e}")
            self.is_index_ready = False

    def _save_index_to_cache(self):
        """Saves the FAISS index and guideline chunks to disk."""
        if not self.faiss_index or not self.guideline_chunks:
            logger.warning("Attempted to save cache, but index or chunks are missing.")
            return

        try:
            faiss.write_index(self.faiss_index, self.index_path)
            with open(self.chunks_path, "wb") as f:
                pickle.dump(self.guideline_chunks, f)
            logger.info(f"Successfully saved index and chunks to '{self.cache_dir}'.")
        except Exception as e:
            logger.error(f"Failed to save index to cache: {e}")

    def _build_index_from_sources(self) -> None:
        """Loads guidelines from a list of local file paths and builds a FAISS index."""
        self.guideline_chunks = []
        for source_path in self.source_paths:
            self.guideline_chunks.extend(self._load_from_local_path(source_path))

        if self.guideline_chunks:
            logger.info("Encoding guidelines into vectors...")
            texts_to_encode = [chunk[0] for chunk in self.guideline_chunks]
            embeddings = self.model.encode(
                texts_to_encode, convert_to_tensor=True, show_progress_bar=True
            )
            embeddings_np = embeddings.cpu().numpy()

            if embeddings_np.dtype != np.float32:
                embeddings_np = embeddings_np.astype(np.float32)

            embedding_dim = embeddings_np.shape[1]
            self.faiss_index = faiss.IndexFlatL2(embedding_dim)
            self.faiss_index.add(embeddings_np)

        self.is_index_ready = True
        logger.info(
            f"Loaded and indexed {len(self.guideline_chunks)} guideline chunks using FAISS."
        )

    @staticmethod
    def _extract_text_from_pdf(
        file_path: str, source_name: str
    ) -> List[Tuple[str, str]]:
        # ... (rest of the file is unchanged)
        """Extracts text from a file, chunking it by paragraph."""
        chunks = []
        try:
            if file_path.lower().endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                paragraphs = text.split("\n\n")
                for para in paragraphs:
                    cleaned_para = para.replace("\n", " ").strip()
                    if cleaned_para:
                        chunks.append((cleaned_para, source_name))
                return chunks

            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        paragraphs = text.split("\n\n")
                        for para in paragraphs:
                            cleaned_para = para.replace("\n", " ").strip()
                            if cleaned_para:
                                chunks.append(
                                    (cleaned_para, f"{source_name} (Page {i+1})")
                                )
        except Exception as e:
            logger.error(f"Failed to extract text from '{file_path}': {e}")
            raise
        return chunks

    def _load_from_local_path(self, file_path: str) -> List[Tuple[str, str]]:
        """Loads and extracts text chunks from a local file."""
        logger.info(f"Parsing guidelines from local file: {file_path}...")
        if not os.path.exists(file_path):
            logger.error(f"Local guideline file not found: {file_path}")
            return []

        source_name = os.path.basename(file_path)
        if file_path.lower().endswith(".json"):
            return self._extract_text_from_json(file_path, source_name)
        return self._extract_text_from_pdf(file_path, source_name)

    @staticmethod
    def _extract_text_from_json(
        file_path: str, source_name: str
    ) -> List[Tuple[str, str]]:
        """Extracts text from a JSON file, assuming a list of objects with specific keys."""
        chunks = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                # Combine the relevant fields into a single string for embedding
                text = f"Title: {item.get('issue_title', '')}. Detail: {item.get('issue_detail', '')}"
                chunks.append((text, source_name))
        except Exception as e:
            logger.error(f"Failed to extract text from '{file_path}': {e}")
            raise
        return chunks

    def search(self, query: str, top_k: int = None) -> List[dict]:
        """Performs a FAISS similarity search through the loaded guidelines."""
        if top_k is None:
            top_k = self.config["retrieval_settings"]["similarity_top_k"]

        if not self.is_index_ready or not self.faiss_index:
            logger.warning("Search called before guidelines were loaded and indexed.")
            return []

        query_embedding = self.model.encode([query], convert_to_tensor=True)
        # Ensure it's a numpy array before continuing
        if not isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.cpu().numpy()

        if query_embedding.dtype != np.float32:
            query_embedding = query_embedding.astype(np.float32)

        distances, indices = self.faiss_index.search(query_embedding, top_k)

        results = []
        for i, dist in zip(indices[0], distances[0]):
            if i != -1:
                chunk = self.guideline_chunks[i]
                results.append({"text": chunk[0], "source": chunk[1], "score": dist})

        return results
