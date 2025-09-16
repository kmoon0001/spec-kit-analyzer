from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Dict, Any

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

class NERService:
    """
    A service for performing Named Entity Recognition (NER) using a transformer model.
    """
    def __init__(self, model_name: str, context_service: Optional[ContextService] = None):
        """
        Initializes the NER service by loading the specified model.

        Args:
            model_name (str): The name of the NER model from the Hugging Face Hub.
            context_service (Optional[ContextService]): An instance of the ContextService for classifying sentences.
        """
        self.model_name = model_name
        self.pipe = None
        self.context_service = context_service
        try:
            logger.info(f"Loading NER model: {self.model_name}")
            # Using AutoModel and AutoTokenizer to ensure compatibility
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForTokenClassification.from_pretrained(self.model_name)
            self.pipe = pipeline(
                "ner",
                model=model,
                tokenizer=tokenizer,
                aggregation_strategy="simple" # This strategy groups sub-word tokens into single entities
            )
            logger.info("NER model loaded successfully.")
        except Exception as e:
            logger.exception(f"Failed to load NER model {self.model_name}: {e}")

    def is_ready(self) -> bool:
        """Check if the NER service is fully initialized and ready to use."""
        return self.pipe is not None

    def _find_sentence_for_entity(self, entity: Dict[str, Any], sentences: List[str], full_text: str) -> str:
        """Finds the full sentence that contains the given entity."""
        # Note: This is a simplified implementation. A more robust solution would
        # build a map of sentence start/end indices to avoid re-calculating.
        char_offset = 0
        for sentence in sentences:
            sentence_start = char_offset
            sentence_end = char_offset + len(sentence)
            if sentence_start <= entity['start'] < sentence_end:
                return sentence
            # Account for the newline character that joins sentences
            char_offset += len(sentence) + 1
        return ""

    def extract_entities(self, text: str, sentences: List[str]) -> List[NEREntity]:
        """
        Extracts named entities from a given text and classifies their context.

        Args:
            text (str): The full text to analyze.
            sentences (List[str]): The text split into a list of sentences.

        Returns:
            List[NEREntity]: A list of found entities, enriched with context.
        """
        if not self.is_ready():
            logger.warning("NER service is not ready. Cannot extract entities.")
            return []

        try:
            logger.info("Extracting entities from text...")
            results = self.pipe(text)

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
                        context=context
                    )
                )

            logger.info(f"Extracted and contextualized {len(enriched_entities)} entities.")
            return enriched_entities
        except Exception as e:
            logger.exception(f"An error occurred during NER entity extraction: {e}")
            return []
