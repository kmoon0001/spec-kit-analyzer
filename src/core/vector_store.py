"""Manages the in-memory vector store for report embeddings using FAISS.

This module provides a singleton-like pattern for a vector store, ensuring that
the FAISS index is initialized once and can be accessed throughout the application.
This is crucial for efficiently finding similar reports based on their embeddings.
"""

import logging
import sqlite3
from typing import Any

# FAISS may not be available in some environments (e.g., Windows py3.13).
# Fall back to a pure-NumPy implementation when not installed.
try:  # pragma: no cover - environment dependent
    import faiss  # type: ignore

    _FAISS_AVAILABLE = True
except Exception:  # pragma: no cover - environment dependent
    faiss = None  # type: ignore
    _FAISS_AVAILABLE = False

import numpy as np
import sqlalchemy
import sqlalchemy.exc

logger = logging.getLogger(__name__)


class VectorStore:
    """A singleton class to manage the FAISS index for report embeddings."""

    _instance: "VectorStore | None" = None

    def __init__(self) -> None:
        # These attributes are set in __new__ but we need to declare them for mypy
        self.embedding_dim: int
        self.index: Any
        self.report_ids: list[int]
        self.is_initialized: bool
        self._fallback_vectors: list[Any]
        self._fallback_ids: list[int]

    def __new__(cls, embedding_dim: int = 768) -> "VectorStore":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize instance attributes (avoiding type assignment to non-self)
            instance = cls._instance
            instance.embedding_dim = embedding_dim
            instance.index = None
            instance.report_ids = []
            cls._instance.is_initialized = False
            # Fallback storage when FAISS is unavailable
            instance._fallback_vectors = []
            instance._fallback_ids = []
        return cls._instance

    def initialize_index(self):
        """Initializes the FAISS index (or fallback arrays when FAISS is missing)."""
        if self.is_initialized:
            logger.info("FAISS index is already initialized.")
            return

        if _FAISS_AVAILABLE:
            try:
                self.index = faiss.IndexFlatL2(self.embedding_dim)
                self.index = faiss.IndexIDMap(self.index)
                self.is_initialized = True
                logger.info("FAISS index initialized with embedding dimension: %s", self.embedding_dim)
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Failed to initialize FAISS index: %s", exc)
                self.is_initialized = False
        else:
            # Use simple in-memory storage with NumPy for distance computations
            self._fallback_vectors = []
            self._fallback_ids = []
            self.is_initialized = True
            logger.info("FAISS not available; using in-memory vector store fallback.")

    def _total_vectors(self) -> int:
        if _FAISS_AVAILABLE and self.index is not None:
            return int(getattr(self.index, "ntotal", 0))
        return len(self._fallback_ids)

    def add_vectors(self, vectors: np.ndarray, ids: list[int]):
        """Adds vectors to the index or the fallback store."""
        if not self.is_initialized:
            logger.warning("Cannot add vectors: vector store is not initialized.")
            return

        if vectors.ndim != 2 or vectors.shape[1] != self.embedding_dim:
            logger.error(
                "Vector dimension mismatch. Expected %s, got %s",
                self.embedding_dim,
                vectors.shape[1] if vectors.ndim == 2 else None,
            )
            return

        try:
            if _FAISS_AVAILABLE and self.index is not None:
                self.index.add_with_ids(vectors.astype("float32"), np.array(ids))
                self.report_ids.extend(ids)
                logger.info("Added %s new vectors to the index. Total vectors: %s", len(ids), self._total_vectors())
            else:
                for vec, vec_id in zip(vectors, ids, strict=False):
                    self._fallback_vectors.append(vec.astype("float32"))
                    self._fallback_ids.append(int(vec_id))
                self.report_ids.extend(ids)
                logger.info("Added %s vectors to fallback store. Total vectors: %s", len(ids), self._total_vectors())
        except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as exc:
            logger.exception("Failed to add vectors to vector store: %s", exc)

    def search(self, query_vector: np.ndarray, k: int, threshold: float = 0.9) -> list[tuple[int, float]]:
        """Searches the index for similar vectors.

        Returns a list of (id, similarity) pairs with similarity in [0,1].
        """
        if not self.is_initialized or self._total_vectors() == 0:
            logger.warning("Cannot search: vector store is not initialized or is empty.")
            return []

        try:
            query = query_vector.astype("float32").reshape(1, -1)
            if _FAISS_AVAILABLE and self.index is not None:
                distances, indices = self.index.search(query, k)
                results: list[tuple[int, float]] = []
                for idx, dist in zip(indices[0], distances[0], strict=False):
                    if idx != -1:  # -1 indicates no result
                        similarity = 1 - (float(dist) / float(self.embedding_dim))
                        if similarity >= threshold:
                            results.append((int(idx), float(similarity)))
                return results
            # Fallback: brute-force L2 nearest neighbors
            stack = np.stack(self._fallback_vectors, axis=0)
            dists = np.linalg.norm(stack - query, axis=1)
            topk_indices = np.argsort(dists)[: max(k, 0)]
            fallback_results: list[tuple[int, float]] = []
            for pos in topk_indices:
                idx = self._fallback_ids[int(pos)]
                dist = float(dists[int(pos)])
                similarity = 1 - (dist / float(self.embedding_dim))
                if similarity >= threshold:
                    fallback_results.append((int(idx), float(similarity)))
            return fallback_results
        except (sqlalchemy.exc.SQLAlchemyError, sqlite3.Error) as exc:
            logger.exception("Failed to search vector store: %s", exc)
            return []


# Global instance of the vector store
vector_store = VectorStore()


def get_vector_store() -> VectorStore:
    """Returns the global instance of the vector store."""
    return vector_store
