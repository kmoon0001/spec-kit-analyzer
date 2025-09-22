from __future__ import annotations

import logging
import sqlite3
from typing import List, Dict, Set, Optional, Callable

from .ner_service import NEREntity
# from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity
# import numpy as np


logger = logging.getLogger(__name__)


def _jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """Calculates the Jaccard similarity between two sets of words."""
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union != 0 else 0


class EntityConsolidationService:
    """
    A service to consolidate and merge NER entities from multiple models.
    """
    def __init__(self, db_connection_provider: Optional[Callable[[], sqlite3.Connection]] = None):
        self.db_connection_provider = db_connection_provider
        self.performance_cache: Dict[tuple[str, str], float] = {}

    def _get_model_weights(self, model_name: str, entity_label: str) -> float:
        """
        Fetches the historical performance of a model for a given label and returns a weight.
        A simple weighting scheme: (confirmations + 1) / (confirmations + rejections + 2)
        The +1/+2 is for Laplace smoothing to avoid zero-division and give a baseline score.
        """
        if not self.db_connection_provider:
            return 0.5 # Default weight if no DB is available

        cache_key = (model_name, entity_label)
        if cache_key in self.performance_cache:
            return self.performance_cache[cache_key]

        try:
            with self.db_connection_provider() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT confirmations, rejections
                    FROM ner_model_performance
                    WHERE model_name = ? AND entity_label = ?
                """, (model_name, entity_label))
                row = cur.fetchone()
                if row:
                    confirmations, rejections = row
                    # Ensure we don't divide by zero if for some reason we have negative values (should not happen)
                    denominator = confirmations + rejections + 2
                    if denominator <= 0:
                        weight = 0.5
                    else:
                        weight = (confirmations + 1) / denominator
                else:
                    weight = 0.5 # Default weight for unseen pairs

                self.performance_cache[cache_key] = weight
                logger.debug(f"Weight for {model_name}/{entity_label}: {weight:.2f}")
                return weight
        except Exception as e:
            logger.warning(f"Could not fetch model performance for {model_name}/{entity_label}: {e}")
            return 0.5 # Default weight on error
    def consolidate_entities(
        self, all_results: Dict[str, List[NEREntity]], original_text: str,
        embedding_model = None
    ) -> List[NEREntity]:
        """
        Placeholder for merging overlapping entities from different models.
        """
        logger.info("EntityConsolidationService.consolidate_entities called, but service is a placeholder. Returning empty list.")
        return []

    def _merge_entity_group(
        self, group: List[NEREntity], original_text: str
    ) -> NEREntity:
        """
        Placeholder for merging a group of overlapping entities.
        """
        # This method will likely not be called if consolidate_entities is a placeholder.
        # Returning the first entity as a safe fallback.
        if not group:
            # This case should ideally not be reached.
            return None
        return group[0]
