
import logging

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer
from sentence_transformers.util import cos_sim

from src.config import get_settings

from .cache_service import cache_service
from .query_expander import QueryExpander

try:  # pragma: no cover - optional dependency during tests
    from src.database import crud
except (sqlalchemy.exc.SQLAlchemyError, ModuleNotFoundError, ImportError, sqlite3.Error):
    crud = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)


class HybridRetriever:
    """Combine keyword, dense retrieval, and reranking with cached embeddings and query expansion."""

    def __init__(self,
                 rules: list[dict[str, str]] | None = None,
                 model_name: str | None = None,
                 query_expander: QueryExpander | None = None) -> None:
        settings = get_settings()
        self.rules = rules or self._load_rules_from_db()

        dense_model_name = getattr(settings.retrieval, "dense_model_name", "pritamdeka/S-PubMedBert-MS-MARCO")
        reranker_model_name = getattr(settings.models, "reranker", "cross-encoder/ms-marco-MiniLM-L-6-v2")

        features_cfg = getattr(settings, "features", {}) or {}
        if isinstance(features_cfg, dict):
            self.use_reranker = bool(features_cfg.get("enable_reranker", False))
            self.use_query_expansion = bool(features_cfg.get("enable_query_expansion", True))
        else:
            self.use_reranker = bool(getattr(features_cfg, "enable_reranker", False))
            self.use_query_expansion = bool(getattr(features_cfg, "enable_query_expansion", True))

        self.dense_retriever = SentenceTransformer(dense_model_name)
        self.reranker = None
        if self.use_reranker and reranker_model_name:
            try:
                self.reranker = CrossEncoder(reranker_model_name)
            except Exception as exc:  # pragma: no cover - optional dependency fallback
                logger.warning("Failed to initialize reranker '%s': %s", reranker_model_name, exc)
                self.use_reranker = False

        # Initialize query expander
        self.query_expander = query_expander or QueryExpander()

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
    def _load_rules_from_db() -> list[dict[str, str]]:
        if crud is None or not hasattr(crud, "get_all_rubrics"):
            return []
        try:
            rubric_models = crud.get_all_rubrics()
        except Exception:
            return []
        return [
            {"id": r.id, "name": getattr(r, "name", ""), "content": getattr(r, "content", ""), "category": getattr(r, "category", "")}
            for r in rubric_models
        ]

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        k: int = 60,
        category_filter: str | None = None,
        discipline: str | None = None,
        document_type: str | None = None,
        context_entities: list[str] | None = None,
    ) -> list[dict[str, str]]:
        if not self.rules or not self.corpus:
            return []

        # 0. Query Expansion (if enabled)
        expanded_query = query
        expansion_result = None

        if self.use_query_expansion:
            try:
                expansion_result = self.query_expander.expand_query(
                    query=query,
                    discipline=discipline,
                    document_type=document_type,
                    context_entities=context_entities,
                )
                expanded_query = expansion_result.get_expanded_query(max_terms=8)
                logger.debug(f"Query expanded from '{query}' to '{expanded_query}' "
                           f"({expansion_result.total_terms} total terms)")
            except Exception as e:
                logger.warning("Query expansion failed, using original query: %s", e)
                expanded_query = query

        # 1. Hybrid Retrieval (BM25 + Dense) with RRF
        tokenized_query = expanded_query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query) if self.bm25 is not None else np.zeros(len(self.rules))
        bm25_ranks = {doc_id: rank + 1 for rank, doc_id in enumerate(np.argsort(bm25_scores)[::-1])}

        # Use expanded query for dense retrieval as well
        query_embedding = self._get_embedding(expanded_query)
        if self.corpus_embeddings is None:
            return []
        dense_scores = cos_sim(query_embedding, self.corpus_embeddings)[0].cpu().numpy()
        dense_ranks = {doc_id: rank + 1 for rank, doc_id in enumerate(np.argsort(dense_scores)[::-1])}

        rrf_scores = {doc_id: 0.0 for doc_id in set(bm25_ranks.keys()) | set(dense_ranks.keys())}
        for doc_id in rrf_scores:
            if doc_id in bm25_ranks:
                rrf_scores[doc_id] += 1 / (k + bm25_ranks[doc_id])
            if doc_id in dense_ranks:
                rrf_scores[doc_id] += 1 / (k + dense_ranks[doc_id])

        # Take a larger set for the reranker to work with (e.g., top 20)
        initial_top_n = min(len(rrf_scores), 20)
        sorted_initial_docs = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)[:initial_top_n]

        # 2. Reranking with Cross-Encoder (use original query for reranking)
        cross_inp = [[query, self.corpus[doc_id]] for doc_id, _ in sorted_initial_docs]

        if self.use_reranker and self.reranker is not None:
            try:
                cross_scores = self.reranker.predict(cross_inp)
                reranked_results = zip([doc_id for doc_id, _ in sorted_initial_docs], cross_scores, strict=False)
                sorted_reranked_docs = sorted(reranked_results, key=lambda item: item[1], reverse=True)
            except Exception as exc:  # pragma: no cover - prediction errors fall back to RRF order
                logger.warning("Reranker prediction failed; falling back to RRF order: %s", exc)
                sorted_reranked_docs = sorted_initial_docs
        else:
            sorted_reranked_docs = sorted_initial_docs

        # 3. Final Selection and Filtering
        final_rules = []
        for doc_id, score in sorted_reranked_docs:
            rule = self.rules[doc_id].copy()
            rule["relevance_score"] = float(score)

            # Add expansion metadata if query expansion was used
            if expansion_result and self.use_query_expansion:
                rule["query_expansion"] = {
                    "original_query": expansion_result.original_query,
                    "expanded_query": expanded_query,
                    "expansion_sources": list(expansion_result.expansion_sources.keys()),
                    "total_expansions": expansion_result.total_terms - 1,
                }

            final_rules.append(rule)

        if category_filter:
            filtered_rules = [rule for rule in final_rules if rule.get("category", "").lower() == category_filter.lower()]
            return filtered_rules[:top_k]

        return final_rules[:top_k]
