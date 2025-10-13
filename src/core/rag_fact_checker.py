"""RAG-based Fact Checker Service for Clinical Compliance Analysis.

This module provides a RAG (Retrieval Augmented Generation) based fact-checking service
that uses semantic similarity and reranking to validate findings against retrieved rules.
It's designed to be more efficient than traditional NLI models while maintaining accuracy.
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
from sentence_transformers import CrossEncoder

from src.core.hybrid_retriever import HybridRetriever
from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RAGFactChecker:
    """RAG-based fact checker using semantic similarity and reranking."""
    
    def __init__(self, retriever: HybridRetriever):
        """Initialize the RAG fact checker.
        
        Args:
            retriever: HybridRetriever instance for rule retrieval
        """
        self.retriever = retriever
        self.reranker: Optional[CrossEncoder] = None
        self._similarity_threshold = 0.7  # Default threshold
        self._rerank_threshold = 0.8  # Default rerank threshold
        
    def load_reranker(self) -> None:
        """Load the cross-encoder reranker model."""
        if self.reranker is None:
            try:
                logger.info("Loading cross-encoder reranker for fact-checking...")
                # Use a lightweight cross-encoder for reranking
                self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
                logger.info("Reranker loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load reranker: {e}")
                self.reranker = None
    
    def is_ready(self) -> bool:
        """Check if the fact checker is ready."""
        return self.retriever is not None
    
    async def check_finding_plausibility(
        self, 
        finding: Dict[str, Any], 
        rule: Dict[str, Any],
        deep_check: bool = False
    ) -> bool:
        """Check if a finding is plausible using RAG-based validation.
        
        Args:
            finding: Dictionary containing finding details
            rule: Dictionary containing rule details
            deep_check: If True, use the same 7B model for deep validation
            
        Returns:
            True if the finding is plausible, False otherwise
        """
        try:
            finding_text = finding.get("problematic_text", "")
            rule_text = rule.get("content", "") or rule.get("regulation", "")
            
            if not finding_text or not rule_text:
                logger.warning("Missing text for RAG fact-checking, assuming plausible")
                return True
            
            # Step 1: Retrieve relevant rules using semantic search
            relevant_rules = await self._retrieve_relevant_rules(finding_text)
            
            # Step 2: Calculate semantic similarity scores
            similarity_scores = await self._calculate_similarity_scores(finding_text, relevant_rules)
            
            # Step 3: Apply similarity threshold
            if not self._meets_similarity_threshold(similarity_scores):
                logger.debug("Finding does not meet similarity threshold")
                return False
            
            # Step 4: Optional reranking for higher confidence
            if deep_check and self.reranker:
                rerank_scores = await self._rerank_findings(finding_text, relevant_rules)
                if not self._meets_rerank_threshold(rerank_scores):
                    logger.debug("Finding does not meet rerank threshold")
                    return False
            
            # Step 5: Deep check with 7B model if requested
            if deep_check:
                return await self._deep_validation_with_llm(finding_text, relevant_rules)
            
            return True
            
        except Exception as e:
            logger.exception(f"Error in RAG fact-checking: {e}")
            return True  # Fail open
    
    async def _retrieve_relevant_rules(self, finding_text: str) -> List[Dict[str, Any]]:
        """Retrieve relevant rules using the hybrid retriever."""
        try:
            # Use the retriever to find relevant rules
            results = await self.retriever.search_rules(
                query=finding_text,
                top_k=settings.retrieval.similarity_top_k,
                discipline=None  # Search across all disciplines
            )
            
            return [rule for rule in results if rule.get("content")]
            
        except Exception as e:
            logger.warning(f"Error retrieving rules: {e}")
            return []
    
    async def _calculate_similarity_scores(
        self, 
        finding_text: str, 
        rules: List[Dict[str, Any]]
    ) -> List[float]:
        """Calculate semantic similarity scores between finding and rules."""
        try:
            # Use the retriever's embedding service for consistency
            finding_embedding = await self.retriever._get_embedding(finding_text)
            
            scores = []
            for rule in rules:
                rule_text = rule.get("content", "")
                if rule_text:
                    rule_embedding = await self.retriever._get_embedding(rule_text)
                    
                    # Calculate cosine similarity
                    similarity = np.dot(finding_embedding, rule_embedding) / (
                        np.linalg.norm(finding_embedding) * np.linalg.norm(rule_embedding)
                    )
                    scores.append(float(similarity))
                else:
                    scores.append(0.0)
            
            return scores
            
        except Exception as e:
            logger.warning(f"Error calculating similarity scores: {e}")
            return [0.0] * len(rules)
    
    def _meets_similarity_threshold(self, scores: List[float]) -> bool:
        """Check if any similarity score meets the threshold."""
        if not scores:
            return True  # No rules to compare against
        
        max_score = max(scores)
        return max_score >= self._similarity_threshold
    
    async def _rerank_findings(
        self, 
        finding_text: str, 
        rules: List[Dict[str, Any]]
    ) -> List[float]:
        """Rerank findings using cross-encoder."""
        if not self.reranker:
            return [0.0] * len(rules)
        
        try:
            scores = []
            for rule in rules:
                rule_text = rule.get("content", "")
                if rule_text:
                    # Create input pairs for cross-encoder
                    pairs = [(finding_text, rule_text)]
                    score = self.reranker.predict(pairs)[0]
                    scores.append(float(score))
                else:
                    scores.append(0.0)
            
            return scores
            
        except Exception as e:
            logger.warning(f"Error in reranking: {e}")
            return [0.0] * len(rules)
    
    def _meets_rerank_threshold(self, scores: List[float]) -> bool:
        """Check if any rerank score meets the threshold."""
        if not scores:
            return True
        
        max_score = max(scores)
        return max_score >= self._rerank_threshold
    
    async def _deep_validation_with_llm(
        self, 
        finding_text: str, 
        rules: List[Dict[str, Any]]
    ) -> bool:
        """Perform deep validation using the 7B LLM model."""
        try:
            from src.core.llm_service import LLMService
            
            llm_service = LLMService()
            
            # Create a focused prompt for validation
            rules_text = "\n".join([rule.get("content", "") for rule in rules[:3]])  # Top 3 rules
            
            prompt = f"""Given the following clinical finding and relevant rules, determine if the finding is plausible:

Finding: {finding_text}

Relevant Rules:
{rules_text}

Is this finding plausible based on the rules? Answer with only "YES" or "NO"."""

            response = await llm_service.generate_response(
                prompt=prompt,
                max_tokens=10,
                temperature=0.1
            )
            
            # Parse response
            response_text = response.strip().upper()
            return "YES" in response_text
            
        except Exception as e:
            logger.warning(f"Error in deep LLM validation: {e}")
            return True  # Fail open
    
    def set_thresholds(self, similarity_threshold: float = 0.7, rerank_threshold: float = 0.8) -> None:
        """Set the thresholds for fact-checking."""
        self._similarity_threshold = similarity_threshold
        self._rerank_threshold = rerank_threshold
        logger.info(f"RAG fact-checker thresholds set: similarity={similarity_threshold}, rerank={rerank_threshold}")
