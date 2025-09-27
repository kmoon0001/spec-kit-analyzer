import os
import json
import logging
import numpy as np
from typing import List, Tuple
import faiss
import joblib
import pdfplumber
from sentence_transformers import SentenceTransformer
from src.core.config import Config

logger = logging.getLogger(__name__)

class GuidelineService:
    """
    Manages loading, indexing, and searching of compliance guidelines using a neural retriever.
    
    Implements caching for the FAISS index and guideline chunks to improve startup time.
    Service for managing and searching guidelines using FAISS.
    """
    
    def __init__(self, config: Config):
        """Initializes the GuidelineService with configuration."""
        self.config = config
        self.model = SentenceTransformer(config.retrieval_settings.embedding_model)
        self.source_paths = config.retrieval_settings.local_sources
        self.cache_dir = config.retrieval_settings.cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.index_path = os.path.join(self.cache_dir, "faiss_index.bin")
        self.chunks_path = os.path.join(self.cache_dir, "chunks.pkl")
        
        self.guideline_chunks: List[Tuple[str, str]] = []
        self.faiss_index = None
        self.is_index_ready = False
        
    def load_guidelines(self):
        """Loads guidelines from configured sources and builds or loads the FAISS index."""
        if self._is_cache_valid():
            logger.info("Loading guidelines from cache...")
            self._load_index_from_cache()
        else:
            logger.info("Building new index from sources...")
            self._build_index_from_sources()
            self._save_index_to_cache()
            
    def _is_cache_valid(self) -> bool:
        """Checks if the cached index is still valid."""
        if not os.path.exists(self.index_path) or not os.path.exists(self.chunks_path):
            return False
            
        # Check if source files are newer than cache
        try:
            cache_time = os.path.getmtime(self.index_path)
            for source_path in self.source_paths:
                if os.path.exists(source_path) and os.path.getmtime(source_path) > cache_time:
                    return False
            return True
        except OSError:
            return False
            
    def _load_index_from_cache(self):
        """Loads the FAISS index and chunks from cache."""
        try:
            self.faiss_index = faiss.read_index(self.index_path)
            with open(self.chunks_path, 'rb') as f:
                self.guideline_chunks = joblib.load(f)
            self.is_index_ready = True
            logger.info(f"Loaded {len(self.guideline_chunks)} chunks from cache")
        except Exception as e:
            logger.error(f"Failed to load from cache: {e}")
            self._build_index_from_sources()
            
    def _build_index_from_sources(self):
        """Builds the FAISS index from source documents."""
        self.guideline_chunks = []
        all_texts = []
        
        for source_path in self.source_paths:
            if not os.path.exists(source_path):
                logger.warning(f"Source file not found: {source_path}")
                continue
                
            try:
                chunks = self._extract_text_chunks(source_path)
                self.guideline_chunks.extend(chunks)
                all_texts.extend([chunk[1] for chunk in chunks])
                logger.info(f"Processed {len(chunks)} chunks from {source_path}")
            except Exception as e:
                logger.error(f"Failed to process {source_path}: {e}")
                
        if not all_texts:
            logger.error("No valid text chunks found in sources")
            return
            
        # Generate embeddings
        logger.info("Generating embeddings...")
        embeddings = self.model.encode(all_texts, show_progress_bar=True)
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings.astype('float32'))
        self.faiss_index.add(embeddings.astype('float32'))
        
        self.is_index_ready = True
        logger.info(f"Built index with {len(all_texts)} chunks")
        
    def _extract_text_chunks(self, file_path: str) -> List[Tuple[str, str]]:
        """Extracts text chunks from a PDF file."""
        chunks = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        # Split into chunks (simple approach)
                        paragraphs = text.split('\n\n')
                        for para in paragraphs:
                            para = para.strip()
                            if len(para) > 50:  # Filter out very short chunks
                                chunks.append((f"{os.path.basename(file_path)}:p{page_num+1}", para))
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            
        return chunks
        
    def _save_index_to_cache(self):
        """Saves the FAISS index and chunks to cache."""
        try:
            faiss.write_index(self.faiss_index, self.index_path)
            with open(self.chunks_path, 'wb') as f:
                joblib.dump(self.guideline_chunks, f)
            logger.info("Saved index to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
            
    def search(self, query: str, k: int = 5) -> List[Tuple[str, str, float]]:
        """Searches for relevant guidelines.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of tuples (source, text, score)
        """
        if not self.is_index_ready:
            logger.error("Index not ready. Call load_guidelines() first.")
            return []
            
        try:
            # Encode query
            query_embedding = self.model.encode([query])
            faiss.normalize_L2(query_embedding.astype('float32'))
            
            # Search
            scores, indices = self.faiss_index.search(query_embedding.astype('float32'), k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.guideline_chunks):
                    source, text = self.guideline_chunks[idx]
                    results.append((source, text, float(score)))
                    
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
            
    def get_stats(self) -> dict:
        """Returns statistics about the loaded guidelines."""
        return {
            'total_chunks': len(self.guideline_chunks),
            'index_ready': self.is_index_ready,
            'cache_dir': self.cache_dir,
            'source_paths': self.source_paths
        }

# Backwards compatibility function
def get_config():
    """Legacy function for backwards compatibility."""
    from src.core.config import get_config
    return get_config()