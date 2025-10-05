
import logging
from typing import Dict, List, Optional

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder
from sentence_transformers.util import cos_sim

from src.config import get_settings
from .cache_service import cache_service

try:  # pragma: no cover - optional dependency during tests
    from src.database import crud
except Exception:  # pragma: no cover - fallback when database layer unavailable
    crud = None


logger = logging.getLogger(__name__)


class HybridRetriever:
    """Combine keyword, dense retrieval, and reranking with cached embeddings."""

    def __init__(self, rules: Optional[List[Dict[str, str]]] = None, model_name: Optional[str] = None) -> None:
        settings = get_settings()
        self.rules = rules or self._load_rules_from_db()
        
        dense_model_name = getattr(settings.retrieval, "dense_model_name", "pritamdeka/S-PubMedBert-MS-MARCO")
        reranker_model_name = getattr(settings.models, "reranker", "cross-encoder/ms-marco-MiniLM-L-6-v2")

        self.dense_retriever = SentenceTransformer(dense_model_name)
        self.reranker = CrossEncoder(reranker_model_name)
        
        self._build_indices()

    def _build_indices(self) -> None:
        self.corpus = [f"{rule['name']}. {rule['content']}" for rule in self.rules]
        tokenized_corpus = [document.lower().split() for document in self.corpus]
        self.bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else None
        self.corpus_embeddings = (
            self.dense_retriever.encode(self.corpus, convert_to_tensor=True)
            if self.corpus
            else None
        )

    @cache_service.disk_cache
    def _get_embedding(self, text: str):
        return self.dense_retriever.encode(text, convert_to_tensor=True)

    async def initialize(self) -> None:
        if self.rules:
            return
        self.rules = self._load_rules_from_db()
        self._build_indices()

    @staticmethod
    def _load_rules_from_db() -> List[Dict[str, str]]:
        if crud is None: return []
        try:
            rubric_models = crud.get_all_rubrics()
        except Exception: return []
        return [
            {"id": r.id, "name": getattr(r, "name", ""), "content": getattr(r, "content", ""), "category": getattr(r, "category", "")}
            for r in rubric_models
        ]

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        k: int = 60,
        category_filter: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        if not self.rules or not self.corpus:
            return []

        # 1. Hybrid Retrieval (BM25 + Dense) with RRF
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query) if self.bm25 is not None else np.zeros(len(self.rules))
        bm25_ranks = {doc_id: rank + 1 for rank, doc_id in enumerate(np.argsort(bm25_scores)[::-1])}

        query_embedding = self._get_embedding(query)
        if self.corpus_embeddings is None: return []
        dense_scores = cos_sim(query_embedding, self.corpus_embeddings)[0].cpu().numpy()
        dense_ranks = {doc_id: rank + 1 for rank, doc_id in enumerate(np.argsort(dense_scores)[::-1])}

        rrf_scores = {doc_id: 0.0 for doc_id in set(bm25_ranks.keys()) | set(dense_ranks.keys())}
        for doc_id in rrf_scores:
            if doc_id in bm25_ranks: rrf_scores[doc_id] += 1 / (k + bm25_ranks[doc_id])
            if doc_id in dense_ranks: rrf_scores[doc_id] += 1 / (k + dense_ranks[doc_id])

        # Take a larger set for the reranker to work with (e.g., top 20)
        initial_top_n = min(len(rrf_scores), 20)
        sorted_initial_docs = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)[:initial_top_n]
        
        # 2. Reranking with Cross-Encoder
        cross_inp = [[query, self.corpus[doc_id]] for doc_id, _ in sorted_initial_docs]
        cross_scores = self.reranker.predict(cross_inp)

        # Combine initial doc IDs with new reranker scores
        reranked_results = zip([doc_id for doc_id, _ in sorted_initial_docs], cross_scores)
        sorted_reranked_docs = sorted(reranked_results, key=lambda item: item[1], reverse=True)

        # 3. Final Selection and Filtering
        final_rules = [self.rules[doc_id] for doc_id, _ in sorted_reranked_docs]

        if category_filter:
            filtered_rules = [rule for rule in final_rules if rule.get("category", "").lower() == category_filter.lower()]
            return filtered_rules[:top_k]

        return final_rules[:top_k]
