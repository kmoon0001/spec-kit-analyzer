from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

logger = logging.getLogger(__name__)

from .context_service import ContextService

@dataclass
class NEREntity:
    """A dataclass to hold information about a single named entity."""
    text: str
    label: str
    score: float
    start: int
    end: int
    context: Optional[str] = None
    models: List[str] = field(default_factory=list)
    llm_validation: Optional[str] = None # e.g., "Confirmed", "Rejected", "Uncertain"

class NERService:
    """
    A service for performing Named Entity Recognition (NER) using multiple transformer models.
    """
    def __init__(self, model_configs: Dict[str, str], context_service: Optional[ContextService] = None):
        """
        Initializes the NER service by loading multiple models.

        Args:
            model_configs (Dict[str, str]): A dictionary where keys are friendly model names
                                             and values are Hugging Face model identifiers.
            context_service (Optional[ContextService]): An instance of the ContextService for classifying sentences.
        """
        self.model_configs = model_configs
        self.pipes: Dict[str, Any] = {}
        self.context_service = context_service

        for name, model_id in self.model_configs.items():
            if model_id == "JSL_MODEL_PLACEHOLDER":
                logger.info(f"Skipping placeholder model '{name}'. User will integrate their JSL model here.")
                continue
            try:
                logger.info(f"Loading NER model '{name}': {model_id}")
                tokenizer = AutoTokenizer.from_pretrained(model_id)
                model = AutoModelForTokenClassification.from_pretrained(model_id)
                self.pipes[name] = pipeline(
                    "ner",
                    model=model,
                    tokenizer=tokenizer,
                    aggregation_strategy="simple"
                )
                logger.info(f"NER model '{name}' loaded successfully.")
            except Exception as e:
                logger.exception(f"Failed to load NER model '{name}': {model_id}: {e}")

    def is_ready(self) -> bool:
        """Check if the NER service has at least one model loaded successfully."""
        return len(self.pipes) > 0

    def _find_sentence_for_entity(self, entity: Dict[str, Any], sentences: List[str], full_text: str) -> str:
        """Finds the full sentence that contains the given entity."""
        char_offset = 0
        for sentence in sentences:
            sentence_start = char_offset
            sentence_end = char_offset + len(sentence)
            if sentence_start <= entity['start'] < sentence_end:
                return sentence
            char_offset += len(sentence) + 1
        return ""

    def extract_entities(self, text: str, sentences: List[str]) -> Dict[str, List[NEREntity]]:
        """
        Extracts named entities from a given text using all loaded models.

        Args:
            text (str): The full text to analyze.
            sentences (List[str]): The text split into a list of sentences.

        Returns:
            Dict[str, List[NEREntity]]: A dictionary where keys are model names and
                                         values are lists of found entities.
        """
        if not self.is_ready():
            logger.warning("NER service is not ready. Cannot extract entities.")
            return {}

        all_results: Dict[str, List[NEREntity]] = {}
        for name, pipe in self.pipes.items():
            try:
                logger.info(f"Extracting entities with model '{name}'...")
                results = pipe(text)

                enriched_entities = []
                for res in results:
                    context = None
                    if self.context_service and self.context_service.is_ready():
                        containing_sentence = self._find_sentence_for_entity(res, sentences, text)
                        if containing_sentence:
                            context = self.context_service.classify_sentence(containing_sentence)

                    enriched_entities.append(
                        NEREntity(
                            text=res['word'],
                            label=res['entity_group'],
                            score=round(float(res['score']), 4),
                            start=res['start'],
                            end=res['end'],
                            context=context,
                            models=[name]
                        )
                    )
                all_results[name] = enriched_entities
                logger.info(f"Model '{name}' extracted {len(enriched_entities)} entities.")
            except Exception as e:
                logger.exception(f"An error occurred during NER extraction with model '{name}': {e}")
                all_results[name] = []

        return all_results
