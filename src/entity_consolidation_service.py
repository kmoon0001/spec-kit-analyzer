from __future__ import annotations

import logging
from typing import List, Dict, Set, Optional

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

    def consolidate_entities(
        self, all_results: Dict[str, List[NEREntity]], original_text: str,
        embedding_model: Optional[SentenceTransformer] = None
    ) -> List[NEREntity]:
        """
        Merges overlapping entities from different models into a single list.

        Args:
            all_results (Dict[str, List[NEREntity]]): The raw output from the NERService.
            original_text (str): The original text that was analyzed.

        Returns:
            List[NEREntity]: A single, consolidated list of entities.
        """
        if not all_results:
            return []

        # Step 1: Flatten all entities into a single list from all models
        all_entities = [entity for model_results in all_results.values() for entity in model_results]

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
            # Check for overlap: an entity overlaps if it starts before the current group ends.
            # We find the group's current end by taking the max 'end' of all entities within it.
            group_end = max(e.end for e in current_merge_group)
            if next_entity.start < group_end:
                current_merge_group.append(next_entity)
            else:
                # No overlap, so the current group is complete. Merge it.
                merged_entity = self._merge_entity_group(current_merge_group, original_text)
                merged_entities.append(merged_entity)
                # Start a new group with the current entity.
                current_merge_group = [next_entity]

        # Process the final group after the loop finishes.
        if current_merge_group:
            merged_entity = self._merge_entity_group(current_merge_group, original_text)
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

    def _merge_entity_group(self, group: List[NEREntity], original_text: str) -> NEREntity:
        """
        Merges a group of overlapping entities. If a significant disagreement in labels
        is found for highly similar text, a 'DISAGREEMENT' entity is created.
        Otherwise, it merges them and boosts the score if multiple models contributed.
        """
        # --- Disagreement Analysis ---
        # Only check for disagreements if there are multiple entities from different models
        unique_labels = {e.label for e in group}
        if len(unique_labels) > 1 and len(group) > 1:
            # Sort by score to compare the top two contenders
            sorted_group = sorted(group, key=lambda e: e.score, reverse=True)
            e1, e2 = sorted_group[0], sorted_group[1]

            # Check for high text similarity but different labels
            text1_set = set(e1.text.lower().split())
            text2_set = set(e2.text.lower().split())
            similarity = _jaccard_similarity(text1_set, text2_set)

            if similarity > 0.75: # High similarity threshold
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
        # --- End Disagreement Analysis ---

        # Find the entity with the highest confidence score in the group
        best_entity = max(group, key=lambda e: e.score)
        final_score = best_entity.score

        # Collect all unique model names from the entities in the group
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
