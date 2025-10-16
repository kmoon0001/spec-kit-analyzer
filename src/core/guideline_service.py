from __future__ import annotations

import importlib
import logging
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

# Optional FAISS dependency with graceful fallback
try:  # pragma: no cover - environment dependent
    import faiss  # type: ignore

    _FAISS_AVAILABLE = True
except Exception:  # pragma: no cover - environment dependent
    faiss = None  # type: ignore
    _FAISS_AVAILABLE = False

import joblib
import numpy as np

from ..config import get_settings as _get_settings

logger = logging.getLogger(__name__)

# Lazy-load the SentenceTransformer to avoid importing it at startup
_DEFAULT_SENTENCE_TRANSFORMER = None
SentenceTransformer = None
_SentenceTransformer_override = None


def get_settings():
    return _get_settings()


def _fallback_hash_embed(text: str, dim: int = 768) -> np.ndarray:
    """Deterministic lightweight embedding for fallback environments."""
    acc = np.zeros(dim, dtype=np.float32)
    for idx, ch in enumerate(text.encode("utf-8")):
        acc[(idx + ch) % dim] += (ch % 7) * 0.01 + 0.001
    norm = np.linalg.norm(acc)
    return acc if norm == 0 else acc / norm


def _get_sentence_transformer_cls():
    """Lazy-loads and returns the SentenceTransformer class, with fallback."""
    global _DEFAULT_SENTENCE_TRANSFORMER, SentenceTransformer
    if SentenceTransformer is None:
        try:
            _module = importlib.import_module("sentence_transformers")
            _DEFAULT_SENTENCE_TRANSFORMER = _module.SentenceTransformer
            SentenceTransformer = _DEFAULT_SENTENCE_TRANSFORMER
        except Exception:  # pragma: no cover - environment dependent

            class _FallbackSentenceTransformer:  # type: ignore
                def __init__(self, _model_name: str) -> None:  # signature-compatible
                    self.model_name = _model_name

                def encode(self, texts, convert_to_numpy: bool | None = None, convert_to_tensor: bool | None = None):
                    if isinstance(texts, str):
                        texts = [texts]
                    embeds = np.stack([_fallback_hash_embed(t) for t in texts], axis=0)
                    return embeds

            _DEFAULT_SENTENCE_TRANSFORMER = _FallbackSentenceTransformer
            SentenceTransformer = _DEFAULT_SENTENCE_TRANSFORMER

    public_module = sys.modules.get("src.guideline_service")
    if public_module is not None:
        patched = getattr(public_module, "SentenceTransformer", None)
        if patched is not None and patched is not _DEFAULT_SENTENCE_TRANSFORMER:
            return patched

    if _SentenceTransformer_override is not None:
        return _SentenceTransformer_override

    return SentenceTransformer


class GuidelineService:
    """Index and search guideline text snippets."""

    def __init__(
        self,
        sources: Sequence[str],
        cache_dir: str | Path = "data",
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        settings = get_settings()
        self.sources = list(sources)
        self.model_name = model_name or settings.models.retriever
        self._cache_dir: Path | None = None
        self._index_path: Path | None = None
        self._chunks_path: Path | None = None

        self.guideline_chunks: list[tuple[str, str]] = []
        self.faiss_index = None
        self._fallback_embeddings: np.ndarray | None = None
        self.model = _get_sentence_transformer_cls()(self.model_name)
        self.is_index_ready = False

        self.cache_dir = cache_dir
        self._load_or_build_index()

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir or Path("data")

    @cache_dir.setter
    def cache_dir(self, value: str | Path) -> None:
        self._cache_dir = Path(value)
        self._index_path = None  # Reset derived paths
        self._chunks_path = None

    @property
    def index_path(self) -> Path:
        return self._index_path or self.cache_dir / "guidelines.index"

    @property
    def chunks_path(self) -> Path:
        return self._chunks_path or self.cache_dir / "guidelines.joblib"

    def _persist_cache_if_ready(self) -> None:
        if self.guideline_chunks:
            cache_dir = self.cache_dir
            cache_dir.mkdir(parents=True, exist_ok=True)
            # Persist FAISS index if available
            try:
                if _FAISS_AVAILABLE and self.faiss_index is not None:
                    faiss.write_index(self.faiss_index, str(self.index_path))
            except Exception as exc:  # pragma: no cover - best-effort persistence
                logger.warning("Failed to write FAISS index: %s", exc)
            # Always persist chunks
            try:
                joblib.dump(self.guideline_chunks, self.chunks_path)
            except Exception as exc:  # pragma: no cover - best-effort persistence
                logger.warning("Failed to write guideline chunks: %s", exc)

    def _load_or_build_index(self) -> None:
        if self._attempt_load_from_cache():
            return
        self._build_index_from_sources()
        self._persist_cache_if_ready()

    def _attempt_load_from_cache(self) -> bool:
        if not self.chunks_path.exists():
            return False
        try:
            self.guideline_chunks = joblib.load(self.chunks_path)
            # Try to load FAISS index if available
            if _FAISS_AVAILABLE and self.index_path.exists():
                try:
                    self.faiss_index = faiss.read_index(str(self.index_path))
                except Exception as exc:  # pragma: no cover
                    logger.warning("Failed to load FAISS index: %s", exc)
                    self.faiss_index = None
            # Prepare fallback embeddings if FAISS not available
            if not _FAISS_AVAILABLE or self.faiss_index is None:
                texts = [text for text, _ in self.guideline_chunks]
                self._fallback_embeddings = self._encode_texts(texts)
            self.is_index_ready = True
            logger.info("Loaded %d guideline chunks from cache", len(self.guideline_chunks))
            return True
        except (FileNotFoundError, PermissionError, OSError) as exc:
            logger.warning("Failed to load guideline cache: %s", exc)
            self.faiss_index = None
            self.guideline_chunks = []
            self._fallback_embeddings = None
            return False

    def _build_index_from_sources(self) -> None:
        chunks: list[tuple[str, str]] = []
        for source in self.sources:
            chunks.extend(self._load_from_source(Path(source)))

        if not chunks:
            logger.warning("No guideline content found; index will remain empty.")
            self.guideline_chunks = []
            self.faiss_index = None
            self._fallback_embeddings = None
            self.is_index_ready = False
            return

        self.guideline_chunks = chunks
        embeddings = self._encode_texts(text for text, _ in chunks)
        dimension = embeddings.shape[1]
        if _FAISS_AVAILABLE:
            try:
                index = faiss.IndexFlatL2(dimension)
                index.add(embeddings)
                self.faiss_index = index
                self._fallback_embeddings = None
                self.is_index_ready = True
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to build FAISS index, using fallback: %s", exc)
                self.faiss_index = None
                self._fallback_embeddings = embeddings
                self.is_index_ready = True
        else:
            self.faiss_index = None
            self._fallback_embeddings = embeddings
            self.is_index_ready = True

    def _load_from_source(self, path: Path) -> list[tuple[str, str]]:
        if not path.exists() or not path.is_file():
            logger.warning("Guideline source %s does not exist", path)
            return []
        if path.suffix.lower() == ".txt":
            return [(line.strip(), path.name) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        logger.warning("Unsupported guideline format for %s", path)
        return []

    def _encode_texts(self, texts: Iterable[str]) -> np.ndarray:
        if hasattr(self.model, "encode"):
            embeddings = self.model.encode(list(texts), convert_to_numpy=True)
            if not isinstance(embeddings, np.ndarray):
                embeddings = np.asarray(embeddings)
            return embeddings.astype(np.float32)
        # Should not happen; fallback
        return np.stack([_fallback_hash_embed(t) for t in texts], axis=0).astype(np.float32)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not self.is_index_ready:
            return []

        # Encode query as 2D array shape (1, dim)
        q = self.model.encode([query], convert_to_tensor=True)
        query_array = np.asarray(q, dtype=np.float32)

        if _FAISS_AVAILABLE and self.faiss_index is not None:
            distances, indices = self.faiss_index.search(query_array, top_k)
            results: list[dict] = []
            for i, dist in zip(indices[0], distances[0], strict=False):
                if i != -1:
                    text, source = self.guideline_chunks[i]
                    results.append({"text": text, "source": source, "score": float(dist)})
            return results

        if self._fallback_embeddings is None or len(self._fallback_embeddings) == 0:
            return []
        dists = np.linalg.norm(self._fallback_embeddings - query_array[0], axis=1)
        order = np.argsort(dists)[: max(0, top_k)]
        results: list[dict] = []
        for idx in order:
            text, source = self.guideline_chunks[int(idx)]
            results.append({"text": text, "source": source, "score": float(dists[int(idx)])})
        return results


def set_sentence_transformer_override(factory) -> None:
    global _SentenceTransformer_override
    _SentenceTransformer_override = factory


__all__ = ["GuidelineService", "set_sentence_transformer_override", "get_settings"]
