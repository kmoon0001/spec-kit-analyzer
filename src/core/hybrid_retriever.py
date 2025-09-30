import logging
from typing import Dict, List, Optional

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

try:  # pragma: no cover - optional dependency during tests
    from src import crud
except Exception:  # pragma: no cover - fallback when database layer unavailable
    crud = None


logger = logging.getLogger(__name__)


class HybridRetriever:
    """Combine keyword and dense retrieval over in-memory rules."""

    def __init__(self, rules: Optional[List[Dict[str, str]]] = None) -> None:
        self.rules = rules or self._load_rules_from_db()
        self.dense_retriever = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        self._build_indices()

    def _build_indices(self) -> None:
        self.corpus = [
            f"{rule['name']}. Regulation: {rule.get('regulation', '')}. Common Pitfalls: {rule.get('common_pitfalls', '')}. Best Practice: {rule.get('best_practice', '')}"
            for rule in self.rules
        ]
        tokenized_corpus = [document.lower().split() for document in self.corpus]
        self.bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else None
        self.corpus_embeddings = (
            self.dense_retriever.encode(self.corpus, convert_to_tensor=True)
            if self.corpus
            else None
        )

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
                "regulation": getattr(r, "regulation", ""),
                "common_pitfalls": getattr(r, "common_pitfalls", ""),
                "best_practice": getattr(r, "best_practice", ""),
                "category": getattr(r, "category", ""),
            }
            for r in rubric_models
        ]
      
    def retrieve(
        self, query: str, top_k: int = 5, category_filter: Optional[str] = None
    ) -> List[Dict[str, str]]:
        from sentence_transformers.util import cos_sim
        if not self.rules:
            return []

        tokenized_query = query.lower().split()
        bm25_scores = (
            self.bm25.get_scores(tokenized_query)
            if self.bm25 is not None
            else np.zeros(len(self.rules))
        )

        query_embedding = self.dense_retriever.encode(query, convert_to_tensor=True)
        if self.corpus_embeddings is None:
            return []
        dense_scores_tensor = cos_sim(query_embedding, self.corpus_embeddings)[0]
        dense_scores = (
            dense_scores_tensor.cpu().numpy()
            if hasattr(dense_scores_tensor, "cpu")
            else np.asarray(dense_scores_tensor)
        )

        combined = []
        for index, rule in enumerate(self.rules):
            bm25_value = float(bm25_scores[index]) if len(bm25_scores) > index else 0.0
            dense_value = (
                float(dense_scores[index]) if len(dense_scores) > index else 0.0
            )
            combined.append((index, bm25_value + dense_value))

        combined.sort(key=lambda item: item[1], reverse=True)
        sorted_rules = [self.rules[index] for index, _ in combined]

        if category_filter:
            filtered_rules = [
                rule
                for rule in sorted_rules
                if rule.get("category", "").lower() == category_filter.lower()
            ]
            return filtered_rules[:top_k]

        return sorted_rules[:top_k]