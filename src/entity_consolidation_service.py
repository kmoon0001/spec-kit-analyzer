from __future__ import annotations

import logging
from typing import List, Dict

from .ner_service import NEREntity

logger = logging.getLogger(__name__)


class EntityConsolidationService:
    """
    A service to consolidate and merge NER entities from multiple models.
    """

    def consolidate_entities(
        self, all_results: Dict[str, List[NEREntity]], original_text: str
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

        logger.info(f"Consolidated {len(all_entities)} raw entities into {len(merged_entities)} merged entities.")
        return merged_entities

    def _merge_entity_group(self, group: List[NEREntity], original_text: str) -> NEREntity:
        """
        Merges a group of overlapping entities into a single, consolidated entity.
        - The new entity spans the full range of the overlapping entities.
        - The label and score are taken from the highest-scoring entity in the group.
        - The list of models is a unique combination of all models in the group.
        """
        # Find the entity with the highest confidence score in the group
        best_entity = max(group, key=lambda e: e.score)

        # Determine the boundaries of the merged entity by finding the min start and max end
        min_start = min(e.start for e in group)
        max_end = max(e.end for e in group)

        # Collect all unique model names from the entities in the group
        models = sorted(list(set(model for e in group for model in e.models)))

        # Create the new merged entity
        merged_entity = NEREntity(
            text=original_text[min_start:max_end],
            label=best_entity.label,  # Use the label from the highest-scoring entity
            score=best_entity.score,  # Use the score from the highest-scoring entity
            start=min_start,
            end=max_end,
            context=best_entity.context, # Carry over the context from the best entity
            models=models,
        )
        return merged_entity
