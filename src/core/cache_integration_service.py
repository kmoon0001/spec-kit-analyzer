"""
Cache integration service for the Therapy Compliance Analyzer.
Demonstrates how to integrate the cache service with the analysis pipeline.
"""

import logging

from .cache_service import (
    DocumentCache,
    EmbeddingCache,
    LLMResponseCache,
    NERCache,
    cleanup_all_caches,
    get_cache_stats,
)

logger = logging.getLogger(__name__)


class CacheIntegrationService:
    """
    Service that integrates caching into the document analysis pipeline.
    Provides cache-aware methods for common AI operations.
    """

    def __init__(self):
        self.cache_hits = 0
        self.cache_misses = 0

    def get_or_compute_embedding(self, text: str, embedding_func) -> list[float]:
        """
        Get embedding from cache or compute and cache it.

        Args:
            text: Text to embed
            embedding_func: Function that computes embeddings

        Returns:
            List of embedding values
        """
        # Try cache first
        cached_embedding = EmbeddingCache.get_embedding(text)
        if cached_embedding is not None:
            self.cache_hits += 1
            logger.debug("Cache hit for embedding (length: %d)", len(text))
            return cached_embedding

        # Compute and cache
        self.cache_misses += 1
        logger.debug("Cache miss for embedding, computing (length: %d)", len(text))
        embedding = embedding_func(text)
        EmbeddingCache.set_embedding(text, embedding)
        return embedding

    def get_or_compute_ner(self, text: str, model_name: str, ner_func) -> list[dict]:
        """
        Get NER results from cache or compute and cache them.

        Args:
            text: Text to analyze
            model_name: Name of the NER model
            ner_func: Function that performs NER

        Returns:
            List of NER entities
        """
        # Try cache first
        cached_ner = NERCache.get_ner_results(text, model_name)
        if cached_ner is not None:
            self.cache_hits += 1
            logger.debug("Cache hit for NER with %s", model_name)
            return cached_ner

        # Compute and cache
        self.cache_misses += 1
        logger.debug("Cache miss for NER with %s, computing", model_name)
        ner_results = ner_func(text)
        NERCache.set_ner_results(text, model_name, ner_results)
        return ner_results

    def get_or_compute_llm_response(
        self, prompt: str, model_name: str, llm_func
    ) -> str:
        """
        Get LLM response from cache or compute and cache it.

        Args:
            prompt: Input prompt
            model_name: Name of the LLM model
            llm_func: Function that calls the LLM

        Returns:
            LLM response text
        """
        # Try cache first
        cached_response = LLMResponseCache.get_llm_response(prompt, model_name)
        if cached_response is not None:
            self.cache_hits += 1
            logger.debug(f"Cache hit for LLM response with {model_name}")
            return cached_response

        # Compute and cache
        self.cache_misses += 1
        logger.debug(f"Cache miss for LLM response with {model_name}, computing")
        response = llm_func(prompt)
        LLMResponseCache.set_llm_response(prompt, model_name, response)
        return response

    def get_or_compute_document_classification(
        self, doc_hash: str, text: str, classify_func
    ) -> dict:
        """
        Get document classification from cache or compute and cache it.

        Args:
            doc_hash: Hash of the document content
            text: Document text
            classify_func: Function that classifies documents

        Returns:
            Classification results dictionary
        """
        # Try cache first
        cached_classification = DocumentCache.get_document_classification(doc_hash)
        if cached_classification is not None:
            self.cache_hits += 1
            logger.debug("Cache hit for document classification")
            return cached_classification

        # Compute and cache
        self.cache_misses += 1
        logger.debug("Cache miss for document classification, computing")
        classification = classify_func(text)
        DocumentCache.set_document_classification(doc_hash, classification)
        return classification

    def get_cache_performance_stats(self) -> dict:
        """Get cache performance statistics."""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0

        cache_stats = get_cache_stats()

        return {
            "hit_rate_percent": round(hit_rate, 2),
            "total_hits": self.cache_hits,
            "total_misses": self.cache_misses,
            "total_requests": total_requests,
            **cache_stats,
        }

    def reset_performance_counters(self):
        """Reset the performance counters."""
        self.cache_hits = 0
        self.cache_misses = 0

    def cleanup_and_report(self):
        """Cleanup caches and log performance report."""
        stats = self.get_cache_performance_stats()
        logger.info(
            f"Cache performance - Hit rate: {stats['hit_rate_percent']}%, "
            f"Memory usage: {stats['memory_usage_mb']:.1f}MB, "
            f"Total entries: {stats['total_entries']}"
        )

        cleanup_all_caches()


# Global cache integration service instance
cache_integration = CacheIntegrationService()
