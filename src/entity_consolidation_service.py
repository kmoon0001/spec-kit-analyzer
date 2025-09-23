from __future__ import annotations

import logging
import sqlite3
from typing import List, Dict, Set, Optional, Callable

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
 
from .ner_service import NEREntity

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
        embedding_model: Optional[SentenceTransformer] = None
    ) -> List[NEREntity]:
        """
        Merges overlapping entities from different models into a single list.

        Args:
            all_results (Dict[str, List[NEREntity]]): The raw output from the
                                                     NERService.
            original_text (str): The original text that was analyzed.
            embedding_model (Optional[SentenceTransformer]): An optional sentence transformer model for semantic merging.

        Returns:
            List[NEREntity]: A single, consolidated list of entities.
        """
        # Clear the performance cache for each new analysis run
        self.performance_cache = {}
        if not all_results:
            return []

        # Step 1: Flatten all entities into a single list from all models
        all_entities = [
            entity for model_results in all_results.values()
            for entity in model_results
        ]

        # Step 2: Sort entities by their start position to process them in order
        all_entities.sort(key=lambda e: e.start)

        if not all_entities:
            return []

        # Step 3: Iterate through sorted entities and merge overlapping ones
        merged_entities: List[NEREntity] = []
        if not all_entities:
            return []

        current_merge_group = [all_entities[0]]

        for i in range(1, len(all_entities)):
            next_entity = all_entities[i]
            
            # Check for overlap: an entity overlaps if it starts before the
            # current group ends. We find the group's current end by taking
            # the max 'end' of all entities within it.
            group_end = max(e.end for e in current_merge_group)
            if next_entity.start < group_end:
                current_merge_group.append(next_entity)
            else:
                # No overlap, so the current group is complete. Merge it.
                merged_entity = self._merge_entity_group(
                    current_merge_group, original_text
                )
                merged_entities.append(merged_entity)
                # Start a new group with the current entity.
                current_merge_group = [next_entity]

        # Process the final group after the loop finishes.
        if current_merge_group:
            merged_entity = self._merge_entity_group(
                current_merge_group, original_text
            )
            merged_entities.append(merged_entity)

        # --- Semantic Merging of Nearby Entities ---
        if embedding_model and len(merged_entities) > 1:
            semantically_merged_entities: List[NEREntity] = []
            processed_indices: Set[int] = set()

            merged_entities.sort(key=lambda e: e.start)

            for i in range(len(merged_entities)):
                if i in processed_indices:
                    continue

                current_entity = merged_entities[i]
                group_for_semantic_merge = [current_entity]

                # Look ahead for potential semantic merges
                for j in range(i + 1, len(merged_entities)):
                    if j in processed_indices:
                        continue

                    next_entity = merged_entities[j]

                    # Define "nearby": within 50 characters and same label
                    if (next_entity.start - current_entity.end) < 50 and next_entity.label == current_entity.label:
                        try:
                            emb1 = embedding_model.encode([current_entity.text])
                            emb2 = embedding_model.encode([next_entity.text])
                            sim = cosine_similarity(emb1, emb2)[0][0]

                            if sim > 0.85:  # High similarity threshold
                                logger.info(f"Found high semantic similarity ({sim:.2f}) between '{current_entity.text}' and '{next_entity.text}'. Grouping for merge.")
                                group_for_semantic_merge.append(next_entity)
                                processed_indices.add(j)
                        except Exception as e:
                            logger.warning(f"Semantic similarity check failed: {e}")

                if len(group_for_semantic_merge) > 1:
                    logger.info(f"Semantically merging {len(group_for_semantic_merge)} entities.")
                    final_merged = self._merge_entity_group(group_for_semantic_merge, original_text)
                    semantically_merged_entities.append(final_merged)
                else:
                    semantically_merged_entities.append(current_entity)

                processed_indices.add(i)

            merged_entities = semantically_merged_entities
        # --- End Semantic Merging ---

        logger.info(f"Consolidated {len(all_entities)} raw entities into {len(merged_entities)} final entities.")
        return merged_entities

    def _merge_entity_group(
        self, group: List[NEREntity], original_text: str
    ) -> NEREntity:
        """
        Merges a group of overlapping entities. It first checks for label disagreements
        and then uses a weighted score to find the best entity, boosting the score
        if multiple models contributed.
        """
        # --- 1. Disagreement Analysis ---
        unique_labels = {e.label for e in group}
        if len(unique_labels) > 1 and len(group) > 1:
            sorted_group = sorted(group, key=lambda e: e.score, reverse=True)
            e1, e2 = sorted_group[0], sorted_group[1]
            text1_set = set(e1.text.lower().split())
            text2_set = set(e2.text.lower().split())
            similarity = _jaccard_similarity(text1_set, text2_set)

            if similarity > 0.75:  # High similarity threshold
                logger.warning(
                    f"Label disagreement found. Model 1 ('{e1.models[0]}') labeled '{e1.text}' as '{e1.label}', "
                    f"while Model 2 ('{e2.models[0]}') labeled '{e2.text}' as '{e2.label}'."
                )
                min_start = min(e.start for e in group)
                max_end = max(e.end for e in group)
                conflicting_labels = f"'{e1.label}' vs '{e2.label}'"
                return NEREntity(
                    text=original_text[min_start:max_end],
                    label="DISAGREEMENT",
                    score=max(e1.score, e2.score),
                    start=min_start,
                    end=max_end,
                    context=f"Conflicting labels found: {conflicting_labels}",
                    models=sorted(list(set(e.models[0] for e in group))),
                )

        # --- 2. Weighted Scoring to find the best entity ---
        weighted_entities = []
        for entity in group:
            if not entity.models:
                continue
            model_name = entity.models[0]
            weight = self._get_model_weights(model_name, entity.label)
            weighted_score = entity.score * weight
            weighted_entities.append((entity, weighted_score))

        if not weighted_entities:
            # Fallback for safety
            best_entity = max(group, key=lambda e: e.score)
        else:
            best_entity_tuple = max(weighted_entities, key=lambda item: item[1])
            best_entity = best_entity_tuple[0]
            logger.info(f"Selected '{best_entity.text}' (label: {best_entity.label}) as best in group based on weighted score.")

        final_score = best_entity.score
        models = sorted(list(set(model for e in group for model in e.models)))

        # If more than one model contributed, boost the confidence score.
        if len(models) > 1:
            confidence_boost = 0.15 * (1 - final_score)
            final_score = min(1.0, final_score + confidence_boost)
            logger.info(f"Boosting score for merged entity '{best_entity.text}' from {best_entity.score:.2f} to {final_score:.2f} due to multi-model confirmation.")

        min_start = min(e.start for e in group)
        max_end = max(e.end for e in group)

        merged_entity = NEREntity(
            text=original_text[min_start:max_end],
            label=best_entity.label,
            score=round(final_score, 4),
            start=min_start,
            end=max_end,
            context=best_entity.context,
            models=models,
        )
        return merged_entity
