"""
Specialized Clinical Named Entity Recognition (NER) service.

This module uses an ensemble of transformer models to extract a wide range of
clinical entities from text, leveraging a sophisticated merging strategy to
resolve overlapping predictions.
"""

import logging
from typing import List, Dict, Any

from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

logger = logging.getLogger(__name__)


class ClinicalNERService:
    """
    A service for high-accuracy clinical entity recognition using an ensemble of models.
    """

    def __init__(self, model_names: List[str]):
        """
        Initializes the clinical NER ensemble.

        Args:
            model_names: A list of model names from the Hugging Face Hub.
        """
        if not model_names:
            raise ValueError("At least one model name must be provided for the NER ensemble.")
        
        self.model_names = model_names
        self.pipelines = self._initialize_pipelines()

    def _initialize_pipelines(self) -> List[pipeline]:
        """Loads the transformer models into NER pipelines."""
        pipelines = []
        for model_name in self.model_names:
            try:
                logger.info(f"Loading clinical NER model: {model_name}")
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForTokenClassification.from_pretrained(model_name)
                pipelines.append(
                    pipeline(
                        "ner",
                        model=model,
                        tokenizer=tokenizer,
                        aggregation_strategy="simple",
                    )
                )
                logger.info(f"Successfully loaded clinical NER model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load NER model {model_name}: {e}", exc_info=True)
        return pipelines

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts and merges clinical entities from the text using the model ensemble.

        Args:
            text: The input text to analyze.

        Returns:
            A merged and deduplicated list of detected clinical entities.
        """
        if not self.pipelines or not text.strip():
            return []

        all_entities = []
        for pipe in self.pipelines:
            try:
                entities = pipe(text)
                if entities:
                    all_entities.extend(entities)
            except Exception as e:
                logger.warning(f"A clinical NER pipeline failed during execution: {e}")

        return self._merge_entities(all_entities)

    def _merge_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merges overlapping entities based on score and span length."""
        if not entities:
            return []

        # Normalize entities to a consistent format
        for entity in entities:
            entity["word"] = (entity.get("word") or "").strip()
            entity["start"] = int(entity.get("start", 0))
            entity["end"] = int(entity.get("end", 0))
            entity["score"] = float(entity.get("score", 0.0))

        # Sort by start position, then by score descending to prioritize higher-confidence entities
        entities.sort(key=lambda e: (e["start"], -e["score"]))

        merged = []
        for entity in entities:
            if not merged or entity["start"] >= merged[-1]["end"]:
                # If no overlap with the last merged entity, just add it
                merged.append(entity)
            else:
                # Handle overlap with the last merged entity
                last_entity = merged[-1]
                # If the new entity completely contains the last one, replace it
                if entity["end"] > last_entity["end"]:
                    if entity["score"] > last_entity["score"]:
                        merged[-1] = entity
                # Otherwise, if scores are comparable, prefer the longer entity
                elif (entity["end"] - entity["start"]) > (last_entity["end"] - last_entity["start"]):
                     if entity["score"] > (last_entity["score"] * 0.8):
                        merged[-1] = entity

        return merged


__all__ = ["ClinicalNERService"]
