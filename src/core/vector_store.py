"""Manage in-memory embeddings for similarity search with optional FAISS support."""
from __future__ import annotations

import logging
import sqlite3
from typing import Any

try:  # pragma: no cover - environment dependent
    import numpy as np
except ModuleNotFoundError as exc:  # pragma: no cover - handled via skip logic
    np = None  # type: ignore[assignment]
    _NUMPY_AVAILABLE = False
    _NUMPY_IMPORT_ERROR = exc
else:  # pragma: no cover - environment dependent
    _NUMPY_AVAILABLE = True
    _NUMPY_IMPORT_ERROR = None

try:  # pragma: no cover - environment dependent
    import faiss  # type: ignore
except Exception:  # pragma: no cover - handled via skip logic
    faiss = None  # type: ignore[assignment]
    _FAISS_AVAILABLE = False
else:  # pragma: no cover - environment dependent
    _FAISS_AVAILABLE = True

logger = logging.getLogger(__name__)


class VectorStore:
    """Singleton-like storage for document embeddings."""

    _instance: "VectorStore" | None = None

    def __new__(cls, embedding_dim: int = 768) -> "VectorStore":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.embedding_dim = embedding_dim
            cls._instance.index = None
            cls._instance.report_ids: list[int] = []
            cls._instance.is_initialized = False
            cls._instance._fallback_vectors: list[Any] = []
            cls._instance._fallback_ids: list[int] = []
        return cls._instance

    def initialize_index(self) -> None:
        """Initialise FAISS index or fallback storage."""
        if self.is_initialized:
            logger.info("FAISS index is already initialized.")
            return

        if _FAISS_AVAILABLE:
            try:
                index = faiss.IndexFlatL2(self.embedding_dim)
                self.index = faiss.IndexIDMap(index)
                self.is_initialized = True
                logger.info("FAISS index initialized with embedding dimension: %s", self.embedding_dim)
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Failed to initialize FAISS index: %s", exc)
                self.index = None
                self.is_initialized = False
        else:
            if not _NUMPY_AVAILABLE:
                logger.warning(
                    "NumPy is unavailable; vector store fallback cannot be initialised."
                )
                self.is_initialized = False
                return

            self._fallback_vectors = []
            self._fallback_ids = []
            self.is_initialized = True
            logger.info("FAISS not available; using in-memory vector store fallback.")

    def _total_vectors(self) -> int:
        if _FAISS_AVAILABLE and self.index is not None:
            return int(getattr(self.index, "ntotal", 0))
        return len(self._fallback_ids)

    def add_vectors(self, vectors: Any, ids: list[int]) -> None:
        """Add embeddings to the store."""
        if not self.is_initialized:
            logger.warning("Cannot add vectors: vector store is not initialized.")
            return

        if _FAISS_AVAILABLE and self.index is not None:
            try:
                self.index.add_with_ids(vectors.astype("float32"), np.array(ids))  # type: ignore[arg-type]
                self.report_ids.extend(ids)
                logger.info("Added %s new vectors to the index. Total vectors: %s", len(ids), self._total_vectors())
            except Exception as exc:  # pragma: no cover - defensive fallback
                logger.exception("Failed to add vectors to vector store: %s", exc)
            return

        if not _NUMPY_AVAILABLE or np is None:
            logger.warning("NumPy is unavailable; skipping add_vectors in fallback mode.")
            return

        if vectors.ndim != 2 or vectors.shape[1] != self.embedding_dim:  # type: ignore[attr-defined]
            logger.error(
                "Vector dimension mismatch. Expected %s, got %s",
                self.embedding_dim,
                vectors.shape[1] if vectors.ndim == 2 else None,  # type: ignore[index]
            )
            return

        for vec, vec_id in zip(vectors, ids, strict=False):
            self._fallback_vectors.append(vec.astype("float32"))
            self._fallback_ids.append(int(vec_id))
        self.report_ids.extend(ids)
        logger.info("Added %s vectors to fallback store. Total vectors: %s", len(ids), self._total_vectors())

    def search(self, query_vector: Any, k: int, threshold: float = 0.9) -> list[tuple[int, float]]:
        """Search for similar embeddings."""
        if not self.is_initialized or self._total_vectors() == 0:
            logger.warning("Cannot search: vector store is not initialized or is empty.")
            return []

        if _FAISS_AVAILABLE and self.index is not None:
            try:
                query = query_vector.astype("float32").reshape(1, -1)
                distances, indices = self.index.search(query, k)
                results: list[tuple[int, float]] = []
                for idx, dist in zip(indices[0], distances[0], strict=False):
                    if idx != -1:
                        similarity = 1 - (float(dist) / float(self.embedding_dim))
                        if similarity >= threshold:
                            results.append((int(idx), float(similarity)))
                return results
            except Exception as exc:  # pragma: no cover - defensive fallback
                logger.exception("Failed to search vector store: %s", exc)
                return []

        if not _NUMPY_AVAILABLE or np is None:
            logger.warning("NumPy is unavailable; skipping search in fallback mode.")
            return []

        try:
            query = query_vector.astype("float32").reshape(1, -1)
            stack = np.stack(self._fallback_vectors, axis=0)
            dists = np.linalg.norm(stack - query, axis=1)
            topk_indices = np.argsort(dists)[: max(k, 0)]
            results: list[tuple[int, float]] = []
            for pos in topk_indices:
                idx = self._fallback_ids[int(pos)]
                dist = float(dists[int(pos)])
                similarity = 1 - (dist / float(self.embedding_dim))
                if similarity >= threshold:
                    results.append((int(idx), float(similarity)))
            return results
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.exception("Failed to search vector store: %s", exc)
            return []


_vector_store = VectorStore()


def get_vector_store() -> VectorStore:
    """Return the global vector store instance."""
    return _vector_store
