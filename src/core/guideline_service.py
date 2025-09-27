# Python
from __future__ import annotations

# Standard library
import json
import logging
import os
import re
import tempfile
import joblib
from typing import List, Tuple

# Third-party
import pdfplumber
import requests
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from ..config import get_config
from ..parsing import parse_guideline_file
import os
import logging
from typing import List, Tuple
import faiss
import joblib
import pdfplumber
from sentence_transformers import SentenceTransformer
from ..config import get_settings

logger = logging.getLogger(__name__)

class GuidelineService:
    """
    Manages loading, indexing, and searching of compliance guidelines using a neural retriever.
    Implements caching for the FAISS index and guideline chunks to improve startup time.
    """

    def __init__(self, sources: List[str], cache_dir: str = "data"):
        """Initializes the GuidelineService."""
        self.config = get_settings()
        model_name = self.config.models.retriever

        self.guideline_chunks: List[Tuple[str, str]] = []
        self.is_index_ready = False
        self.faiss_index = None

        self.cache_dir = cache_dir
        self.index_path = os.path.join(self.cache_dir, "guidelines.index")
        self.chunks_path = os.path.join(self.cache_dir, "guidelines.joblib")
        self.source_paths = sources

        logger.info(f"Loading Sentence Transformer model: {model_name}")
        self.model = SentenceTransformer(model_name)

        self._load_or_build_index()
        logger.info("GuidelineService initialized.")

    def _load_or_build_index(self):
        """Loads an existing index if available, otherwise builds a new one."""
        if self._cache_exists() and self._cache_valid():
            logger.info("Loading guidelines from cache...")
            self._load_from_cache()
        else:
            logger.info("Cache miss or invalid. Building new index...")
            self._build_index()
            self._save_to_cache()

    def _cache_exists(self) -> bool:
        """Checks if both index and chunks cache files exist."""
        return os.path.exists(self.index_path) and os.path.exists(self.chunks_path)

    def _cache_valid(self) -> bool:
        """Validates cache by checking if source files are newer than cache."""
        if not self._cache_exists():
            return False
        
        cache_time = min(os.path.getmtime(self.index_path), os.path.getmtime(self.chunks_path))
        
        for source_path in self.source_paths:
            if os.path.exists(source_path) and os.path.getmtime(source_path) > cache_time:
                logger.info(f"Source file {source_path} is newer than cache")
                return False
        return True

    def _load_from_cache(self):
        """Loads the FAISS index and guideline chunks from cache."""
        try:
            self.faiss_index = faiss.read_index(self.index_path)
            self.guideline_chunks = joblib.load(self.chunks_path)
            self.is_index_ready = True
            logger.info(f"Loaded {len(self.guideline_chunks)} guideline chunks from cache")
        except Exception as e:
            logger.error(f"Failed to load from cache: {e}")
            self._build_index()
            self._save_to_cache()

    def _save_to_cache(self):
        """Saves the current FAISS index and chunks to cache."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        try:
            faiss.write_index(self.faiss_index, self.index_path)
            joblib.dump(self.guideline_chunks, self.chunks_path)
            logger.info("Saved guidelines to cache")
        except Exception as e:
            logger.error(f"Failed to save to cache: {e}")

    def _build_index(self):
        """Builds the FAISS index from scratch by loading and processing source files."""
        all_chunks = []
        
        for source_path in self.source_paths:
            if source_path.startswith(('http://', 'https://')):
                chunks = self._load_from_url(source_path)
            else:
                chunks = self._load_from_local_path(source_path)
            all_chunks.extend(chunks)
        
        if not all_chunks:
            logger.warning("No guideline chunks loaded. Index will be empty.")
            self.guideline_chunks = []
            self.is_index_ready = False
            return
        
        self.guideline_chunks = all_chunks
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
        texts = [chunk[0] for chunk in all_chunks]
        embeddings = self.model.encode(texts, convert_to_tensor=True, show_progress_bar=True)
        
        # Convert to numpy if needed
        if not isinstance(embeddings, np.ndarray):
            embeddings = embeddings.cpu().numpy()
        
        # Ensure float32 for FAISS
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product similarity
        faiss.normalize_L2(embeddings)  # Normalize for cosine similarity
        self.faiss_index.add(embeddings)
        
        self.is_index_ready = True
        logger.info(f"Built FAISS index with {self.faiss_index.ntotal} vectors")

    def _load_from_url(self, url: str) -> List[Tuple[str, str]]:
        """Downloads and extracts text chunks from a URL."""
        logger.info(f"Downloading guidelines from URL: {url}...")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name
            
            try:
                source_name = url.split('/')[-1] or 'downloaded_guidelines.pdf'
                chunks = self._extract_text_from_pdf(temp_path, source_name)
                return chunks
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Failed to download from '{url}': {e}")
            raise

    def _extract_text_from_pdf(self, file_path: str, source_name: str) -> List[Tuple[str, str]]:
        """Extracts text from a PDF file and returns chunks with source information."""
        chunks = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    # Split into paragraphs and clean
                    paragraphs = re.split(r'\n\s*\n', text)
                    for para in paragraphs:
                        cleaned_para = para.replace('\n', ' ').strip()
                        if cleaned_para:
                            chunks.append((cleaned_para, f"{source_name} (Page {i+1})"))
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
        if file_path.lower().endswith('.json'):
            return self._extract_text_from_json(file_path, source_name)
        return self._extract_text_from_pdf(file_path, source_name)

    def _extract_text_from_json(self, file_path: str, source_name: str) -> List[Tuple[str, str]]:
        """Extracts text from a JSON file, assuming a list of objects with specific keys."""
        chunks = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for item in data:
                text = f"Title: {item.get('issue_title', '')}. Detail: {item.get('issue_detail', '')}"
                chunks.append((text, source_name))
        except Exception as e:
            logger.error(f"Failed to extract text from '{file_path}': {e}")
            raise
        return chunks

    def search(self, query: str, top_k: int = None) -> List[dict]:
        """Performs a FAISS similarity search through the loaded guidelines."""
        if top_k is None:
            top_k = self.config.retrieval_settings.similarity_top_k

        if not self.is_index_ready or not self.faiss_index:
            logger.warning("Search called before guidelines were loaded and indexed.")
            return []

        query_embedding = self.model.encode([query], convert_to_tensor=True)
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

    def parse_guideline_file(file_path: str) -> List[Tuple[str, str]]:
        """Mock function to parse a guideline file. Returns an empty list."""
        return []