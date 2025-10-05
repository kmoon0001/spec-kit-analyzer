"""
Manages the in-memory vector store for report embeddings using FAISS.

This module provides a singleton-like pattern for a vector store, ensuring that
the FAISS index is initialized once and can be accessed throughout the application.
This is crucial for efficiently finding similar reports based on their embeddings.
"""

import logging
import numpy as np
import faiss
from typing import List, Tuple

logger = logging.getLogger(__name__)

class VectorStore:
    """A singleton class to manage the FAISS index for report embeddings."""
    _instance = None

    def __new__(cls, embedding_dim: int = 768):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            cls._instance.embedding_dim = embedding_dim
            cls._instance.index = None
            cls._instance.report_ids = []
            cls._instance.is_initialized = False
        return cls._instance

    def initialize_index(self):
        """Initializes the FAISS index."""
        if self.is_initialized:
            logger.info("FAISS index is already initialized.")
            return

        try:
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.index = faiss.IndexIDMap(self.index)
            self.is_initialized = True
            logger.info(f"FAISS index initialized with embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Failed to initialize FAISS index: {e}")
            self.is_initialized = False

    def add_vectors(self, vectors: np.ndarray, ids: List[int]):
        """Adds vectors to the index."""
        if not self.is_initialized:
            logger.warning("Cannot add vectors: FAISS index is not initialized.")
            return

        if vectors.shape[1] != self.embedding_dim:
            logger.error(f"Vector dimension mismatch. Expected {self.embedding_dim}, got {vectors.shape[1]}")
            return

        try:
            self.index.add_with_ids(vectors.astype('float32'), np.array(ids))
            self.report_ids.extend(ids)
            logger.info(f"Added {len(ids)} new vectors to the index. Total vectors: {self.index.ntotal}")
        except Exception as e:
            logger.error(f"Failed to add vectors to FAISS index: {e}")

    def search(self, query_vector: np.ndarray, k: int, threshold: float = 0.9) -> List[Tuple[int, float]]:
        """Searches the index for similar vectors."""
        if not self.is_initialized or self.index.ntotal == 0:
            logger.warning("Cannot search: FAISS index is not initialized or is empty.")
            return []

        try:
            distances, indices = self.index.search(query_vector.astype('float32'), k)
            results = []
            for i, dist in zip(indices[0], distances[0]):
                if i != -1:  # -1 indicates no result
                    # The distance is L2, so we can convert it to a similarity score
                    # This is a simple linear conversion; a more sophisticated one might be needed
                    similarity = 1 - (dist / self.embedding_dim)
                    if similarity >= threshold:
                        results.append((i, similarity))
            return results
        except Exception as e:
            logger.error(f"Failed to search FAISS index: {e}")
            return []

# Global instance of the vector store
vector_store = VectorStore()

def get_vector_store() -> VectorStore:
    """Returns the global instance of the vector store."""
    return vector_store
