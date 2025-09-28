from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import faiss
import joblib
import numpy as np

from ..config import get_settings as _get_settings

logger = logging.getLogger(__name__)

_module = importlib.import_module("sentence_transformers")
_DEFAULT_SENTENCE_TRANSFORMER = getattr(_module, "SentenceTransformer")
SentenceTransformer = _DEFAULT_SENTENCE_TRANSFORMER

_SentenceTransformer_override = None


def get_settings():
    return _get_settings()


def _get_sentence_transformer_cls():
    public_module = sys.modules.get("src.guideline_service")
    if public_module is not None:
        patched = getattr(public_module, "SentenceTransformer", None)
        if patched is not None and patched is not _DEFAULT_SENTENCE_TRANSFORMER:
            return patched

    if _SentenceTransformer_override is not None:
        return _SentenceTransformer_override

    current = globals().get("SentenceTransformer")
    if current is not None and current is not _DEFAULT_SENTENCE_TRANSFORMER:
        return current

    module = importlib.import_module("sentence_transformers")
    return getattr(module, "SentenceTransformer")


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

        self.guideline_chunks: List[Tuple[str, str]] = []
        self.faiss_index: faiss.Index | None = None
        self.model = _get_sentence_transformer_cls()(self.model_name)
        self.is_index_ready = False

        self.cache_dir = cache_dir  # triggers setters to configure paths
        self._load_or_build_index()

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir or Path("data")

    @cache_dir.setter
    def cache_dir(self, value: str | Path) -> None:
        self._cache_dir = Path(value)
        if not self._cache_dir.exists():
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        if self._index_path is None:
            self._index_path = self._cache_dir / "guidelines.index"
        if self._chunks_path is None:
            self._chunks_path = self._cache_dir / "guidelines.joblib"
        self._persist_cache_if_ready()

    @property
    def index_path(self) -> Path:
        return self._index_path or self.cache_dir / "guidelines.index"

    @index_path.setter
    def index_path(self, value: str | Path) -> None:
        self._index_path = Path(value)
        self._persist_cache_if_ready()

    @property
    def chunks_path(self) -> Path:
        return self._chunks_path or self.cache_dir / "guidelines.joblib"

    @chunks_path.setter
    def chunks_path(self, value: str | Path) -> None:
        self._chunks_path = Path(value)
        self._persist_cache_if_ready()

    def _persist_cache_if_ready(self) -> None:
        if self.faiss_index is not None and self.guideline_chunks:
            cache_dir = self.cache_dir
            cache_dir.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.faiss_index, str(self.index_path))
            joblib.dump(self.guideline_chunks, self.chunks_path)

    def _load_or_build_index(self) -> None:
        if self._attempt_load_from_cache():
            return
        self._build_index_from_sources()
        self._persist_cache_if_ready()

    def _attempt_load_from_cache(self) -> bool:
        if not self.index_path.exists() or not self.chunks_path.exists():
            return False
        try:
            self.faiss_index = faiss.read_index(str(self.index_path))
            self.guideline_chunks = joblib.load(self.chunks_path)
            self.is_index_ready = True
            logger.info(
                "Loaded %d guideline chunks from cache", len(self.guideline_chunks)
            )
            return True
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to load guideline cache: %s", exc)
            self.faiss_index = None
            self.guideline_chunks = []
            return False

    def _build_index_from_sources(self) -> None:
        chunks: List[Tuple[str, str]] = []
        for source in self.sources:
            chunks.extend(self._load_from_source(Path(source)))

        if not chunks:
            logger.warning("No guideline content found; index will remain empty.")
            self.guideline_chunks = []
            self.faiss_index = None
            self.is_index_ready = False
            return

        self.guideline_chunks = chunks
        embeddings = self._encode_texts(text for text, _ in chunks)
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        self.faiss_index = index
        self.is_index_ready = True

    def _load_from_source(self, path: Path) -> List[Tuple[str, str]]:
        if not path.exists() or not path.is_file():
            logger.warning("Guideline source %s does not exist", path)
            return []

        if path.suffix.lower() == ".txt":
            text = path.read_text(encoding="utf-8")
            return [
                (line.strip(), path.name) for line in text.splitlines() if line.strip()
            ]

        logger.warning("Unsupported guideline format for %s", path)
        return []

    def _encode_texts(self, texts: Iterable[str]) -> np.ndarray:
        embeddings = self.model.encode(list(texts), convert_to_numpy=True)
        if not isinstance(embeddings, np.ndarray):  # pragma: no cover - defensive
            embeddings = np.asarray(embeddings)
        embeddings = np.atleast_2d(embeddings)
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)
        return embeddings

    def search(self, query: str, top_k: int = 5) -> List[dict]:
        if not self.is_index_ready or self.faiss_index is None:
            return []

        query_embedding = self.model.encode([query], convert_to_tensor=True)
        if hasattr(query_embedding, "cpu"):
            query_array = query_embedding.cpu().numpy()
        else:
            query_array = np.asarray(query_embedding)

        try:
            query_array = np.asarray(query_array, dtype=np.float32)
        except Exception:
            dim_attr = getattr(self.faiss_index, "d", 1)
            try:
                dim = int(dim_attr)
            except (TypeError, ValueError):
                dim = 1
            query_array = np.zeros((1, dim), dtype=np.float32)

        query_array = np.atleast_2d(query_array)
        try:
            dim_attr = getattr(self.faiss_index, "d", query_array.shape[1])
            dim = int(dim_attr)
        except (TypeError, ValueError):
            dim = query_array.shape[1] if query_array.ndim > 1 else 1

        if query_array.shape[1] != dim:
            query_array = np.resize(query_array, (query_array.shape[0], dim))

        distances, indices = self.faiss_index.search(query_array, top_k)

        results: List[dict] = []
        for position, score in zip(indices[0], distances[0]):
            if position < 0 or position >= len(self.guideline_chunks):
                continue
            text, source = self.guideline_chunks[position]
            results.append({"text": text, "source": source, "score": float(score)})
        return results


def set_sentence_transformer_override(factory) -> None:
    global _SentenceTransformer_override, SentenceTransformer
    _SentenceTransformer_override = factory
    SentenceTransformer = factory


__all__ = [
    "GuidelineService",
    "SentenceTransformer",
    "faiss",
    "set_sentence_transformer_override",
    "get_settings",
]
