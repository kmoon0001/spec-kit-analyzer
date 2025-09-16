from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Dict, Any

from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

logger = logging.getLogger(__name__)

@dataclass
class NEREntity:
    """A dataclass to hold information about a single named entity."""
    text: str
    label: str
    score: float
    start: int
    end: int

class NERService:
    """
    A service for performing Named Entity Recognition (NER) using a transformer model.
    """
    def __init__(self, model_name: str):
        """
        Initializes the NER service by loading the specified model.

        Args:
            model_name (str): The name of the NER model from the Hugging Face Hub.
        """
        self.model_name = model_name
        self.pipe = None
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

    def extract_entities(self, text: str) -> List[NEREntity]:
        """
        Extracts named entities from a given text.

        Args:
            text (str): The text to analyze.

        Returns:
            List[NEREntity]: A list of found entities.
        """
        if not self.is_ready():
            logger.warning("NER service is not ready. Cannot extract entities.")
            return []

        try:
            logger.info("Extracting entities from text...")
            # The pipeline returns a list of dictionaries.
            # Example: {'entity_group': 'DISEASE', 'score': 0.99, 'word': 'cancer', 'start': 20, 'end': 26}
            results = self.pipe(text)

            # Convert the raw results into a list of our structured dataclass
            entities = [
                NEREntity(
                    text=res['word'],
                    label=res['entity_group'],
                    score=round(float(res['score']), 4),
                    start=res['start'],
                    end=res['end']
                )
                for res in results
            ]

            logger.info(f"Extracted {len(entities)} entities.")
            return entities
        except Exception as e:
            logger.exception(f"An error occurred during NER entity extraction: {e}")
            return []
