"""
Specialized Clinical Named Entity Recognition (NER) service.

This module uses an ensemble of transformer models to extract a wide range of
clinical entities from text, leveraging a sophisticated merging strategy to
resolve overlapping predictions.
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional

from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from src.core.cache_service import NERCache

logger = logging.getLogger(__name__)

try:
    from presidio_analyzer import AnalyzerEngine  # type: ignore

    PRESIDIO_AVAILABLE = True
except ImportError:
    AnalyzerEngine = None  # type: ignore
    PRESIDIO_AVAILABLE = False

def get_presidio_wrapper():
    """Return a Presidio AnalyzerEngine if available."""
    if PRESIDIO_AVAILABLE and AnalyzerEngine is not None:
        try:
            return AnalyzerEngine()
        except Exception:
            return None
    return None



class ClinicalNERService:
    """
    A service for high-accuracy clinical entity recognition using an ensemble of models.
    """

    def __init__(self, model_names: Optional[List[str]] = None):
        """
        Initializes the clinical NER ensemble.

        Args:
            model_names: Optional list of model names from the Hugging Face Hub.
        """
        self.model_names = list(model_names or [])
        self.pipelines = self._initialize_pipelines()

    def _initialize_pipelines(self) -> List[Any]:
        """Loads the transformer models into NER pipelines."""
        pipelines = []
        for model_name in self.model_names:
            try:
                logger.info(f"Loading clinical NER model: {model_name}")
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForTokenClassification.from_pretrained(model_name)
                pipelines.append(
                    pipeline(  # type: ignore[call-overload]
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

        # Check cache first for performance optimization
        model_identifier = "_".join(self.model_names) if self.model_names else "default_ner"
        cached_results = NERCache.get_ner_results(text, model_identifier)
        if cached_results is not None:
            logger.debug(f"Cache hit for NER results (model: {model_identifier})")
            return cached_results

        start_time = time.time()
        all_entities = []
        for pipe in self.pipelines:
            try:
                entities = pipe(text)
                if entities:
                    all_entities.extend(entities)
            except Exception as e:
                logger.warning(f"A clinical NER pipeline failed during execution: {e}")

        merged_entities = self._merge_entities(all_entities)
        
        # Cache the results for future use
        processing_time = time.time() - start_time
        ttl_hours = 24.0 if processing_time > 2.0 else 48.0  # Longer TTL for quick processing
        NERCache.set_ner_results(text, model_identifier, merged_entities, ttl_hours)
        
        logger.debug(f"NER processing completed in {processing_time:.2f}s, cached with TTL {ttl_hours}h")
        return merged_entities

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

        merged: List[Dict[str, Any]] = []
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



class NERPipeline(ClinicalNERService):
    """Convenience wrapper around ClinicalNERService with sensible defaults."""

    DEFAULT_MODELS = [
        "d4data/biomedical-ner-all",
        "Clinical-AI-Apollo/Medical-NER",
    ]

    def __init__(self, model_names: Optional[List[str]] = None) -> None:
        if model_names is None:
            model_names = self.DEFAULT_MODELS
        super().__init__(model_names)


class NERAnalyzer:
    """High-level analyzer that wraps NER pipelines with helper utilities."""

    def __init__(self, model_names: Optional[List[str]] = None) -> None:
        self.ner_pipeline = NERPipeline(model_names)
        self.presidio_wrapper = get_presidio_wrapper()
        self.clinical_patterns: Dict[str, str] = {
            "titles": r"(?:Dr\.|DPT|PT|OT|MD|PA|NP|RN|DO|PTA|OTA)",
            "signature_keywords": r"(?:signed|signature|therapist|provider|attending)",
            "name_pattern": r"(?P<name>[A-Z][a-z]+\s+[A-Z][a-z]+)",
        }

    def extract_entities(self, text: Optional[str]) -> List[Dict[str, Any]]:
        if not isinstance(text, str) or not text.strip():
            return []
        try:
            entities = self.ner_pipeline.extract_entities(text)
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.warning("NER extraction failed: %s", exc)
            return []
        return self._deduplicate_entities(entities)

    def extract_clinician_name(self, text: Optional[str]) -> List[str]:
        if not isinstance(text, str) or not text.strip():
            return []
        titles_regex = re.compile(self.clinical_patterns["titles"], re.IGNORECASE)
        signature_regex = re.compile(self.clinical_patterns["signature_keywords"], re.IGNORECASE)
        name_regex = re.compile(self.clinical_patterns["name_pattern"])

        matches = []
        for match in name_regex.finditer(text):
            window_start = max(0, match.start() - 64)
            context_window = text[window_start:match.start()]
            if titles_regex.search(context_window) or signature_regex.search(context_window):
                matches.append(match.group("name").strip())
        return matches

    def extract_medical_entities(self, text: Optional[str]) -> Dict[str, List[str]]:
        categories: Dict[str, List[str]] = {
            "conditions": [],
            "medications": [],
            "procedures": [],
            "anatomy": [],
            "measurements": [],
            "persons": [],
            "other": [],
        }
        for entity in self.extract_entities(text):
            group = (entity.get("entity_group") or "").lower()
            word = entity.get("word", "").strip()
            if not word:
                continue
            if "drug" in group or "med" in group:
                categories["medications"].append(word)
            elif any(keyword in group for keyword in ("disease", "condition", "diagnosis")):
                categories["conditions"].append(word)
            elif "procedure" in group or "treatment" in group:
                categories["procedures"].append(word)
            elif "anatom" in group or "body" in group:
                categories["anatomy"].append(word)
            elif "measure" in group or "value" in group:
                categories["measurements"].append(word)
            elif "person" in group or "name" in group:
                categories["persons"].append(word)
            else:
                categories["other"].append(word)
        return categories

    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        deduped: List[Dict[str, Any]] = []
        for entity in entities:
            key = (
                entity.get("start"),
                entity.get("end"),
                entity.get("word"),
                entity.get("entity_group"),
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(entity)
        return deduped


__all__ = ["ClinicalNERService", "NERPipeline", "NERAnalyzer"]
