
import logging
from typing import Dict, List, Optional

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from src.config import get_settings
from .cache_service import cache_service

try:  # pragma: no cover - optional dependency during tests
    from src.database import crud
except Exception:  # pragma: no cover - fallback when database layer unavailable
    crud = None


logger = logging.getLogger(__name__)


class HybridRetriever:
    """Combine keyword and dense retrieval over in-memory rules with cached embeddings."""

    def __init__(self, rules: Optional[List[Dict[str, str]]] = None, model_name: Optional[str] = None) -> None:
        settings = get_settings()
        self.rules = rules or self._load_rules_from_db()
        dense_model = model_name or getattr(settings.retrieval, "dense_model_name", None)
        if not dense_model:
            dense_model = getattr(settings.models, "retriever", "sentence-transformers/all-MiniLM-L6-v2")
        self.model_name = dense_model
        self.dense_retriever = SentenceTransformer(self.model_name)
        self._build_indices()

    def _build_indices(self) -> None:
        self.corpus = [f"{rule['name']}. {rule['content']}" for rule in self.rules]
        tokenized_corpus = [document.lower().split() for document in self.corpus]
        logger.debug("Hybrid retriever using model", model=self.model_name)
        self.bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else None
        # Corpus embeddings are a one-time cost at startup, so we don't cache them to avoid complexity
        # with dynamic rule updates. Query embeddings, however, are cached.
        self.corpus_embeddings = (
            self.dense_retriever.encode(self.corpus, convert_to_tensor=True)
            if self.corpus
            else None
        )

    @cache_service.disk_cache
    def _get_embedding(self, text: str):
        """Cached method to get sentence embeddings."""
        logger.debug(f"Cache miss for embedding: '{text[:50]}...'")
        return self.dense_retriever.encode(text, convert_to_tensor=True)

    async def initialize(self) -> None:
        if self.rules:
            return
        self.rules = self._load_rules_from_db()
        self._build_indices()

    @staticmethod
    def _load_rules_from_db() -> List[Dict[str, str]]:
        if crud is None:
            logger.warning(
                "HybridRetriever instantiated without database CRUD layer; returning empty rules."
            )
            return []
        try:
            rubric_models = crud.get_all_rubrics()  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover - defensive fallback
            return []
        return [
            {
                "id": r.id,
                "name": getattr(r, "name", ""),
                "content": getattr(r, "content", ""),
                "category": getattr(r, "category", ""),
            }
            for r in rubric_models
        ]

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        k: int = 60,
        category_filter: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Retrieve and rank rules using a hybrid approach with Reciprocal Rank Fusion (RRF).

        Args:
            query (str): The search query.
            top_k (int): The number of top results to return.
            k (int): The ranking constant for RRF. Defaults to 60.
            category_filter (Optional[str]): A filter for the rule category (currently ignored).

        Returns:
            List[Dict[str, str]]: A list of the top-k rules.
        """
        if category_filter:
            logger.warning(
                "The 'category_filter' is not yet implemented with RRF and will be ignored."
            )
        if not self.rules or not self.corpus:
            return []

        # 1. Get BM25 scores and ranks
        tokenized_query = query.lower().split()
        bm25_scores = (
            self.bm25.get_scores(tokenized_query)
            if self.bm25 is not None
            else np.zeros(len(self.rules))
        )
        bm25_ranks = {
            doc_id: rank + 1
            for rank, doc_id in enumerate(np.argsort(bm25_scores)[::-1])
        }

        # 2. Get dense retrieval scores and ranks using the cached embedding function
        query_embedding = self._get_embedding(query)
        if self.corpus_embeddings is None:
            return []
        dense_scores_tensor = cos_sim(query_embedding, self.corpus_embeddings)[0]
        dense_scores = (
            dense_scores_tensor.cpu().numpy()
            if hasattr(dense_scores_tensor, "cpu")
            else np.asarray(dense_scores_tensor)
        )
        dense_ranks = {
            doc_id: rank + 1
            for rank, doc_id in enumerate(np.argsort(dense_scores)[::-1])
        }

        # 3. Calculate RRF scores
        rrf_scores = {}
        all_doc_ids = set(bm25_ranks.keys()) | set(dense_ranks.keys())

        for doc_id in all_doc_ids:
            rrf_score = 0.0
            if doc_id in bm25_ranks:
                rrf_score += 1 / (k + bm25_ranks[doc_id])
            if doc_id in dense_ranks:
                rrf_score += 1 / (k + dense_ranks[doc_id])
            rrf_scores[doc_id] = rrf_score

        # 4. Sort by RRF score and return top-k results
        sorted_docs = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)
        sorted_rules = [self.rules[doc_id] for doc_id, _ in sorted_docs]

        if category_filter:
            filtered_rules = [
                rule
                for rule in sorted_rules
                if rule.get("category", "").lower() == category_filter.lower()
            ]
            return filtered_rules[:top_k]

        return sorted_rules[:top_k]
