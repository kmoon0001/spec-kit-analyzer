import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class NERPipeline:
    """A pipeline for Named Entity Recognition that combines multiple models."""

    def __init__(self, model_names: List[str]):
        self.model_names = model_names
        self.pipelines = []
        self._load_models()

    def _load_models(self):
        """Lazy-loads the NER models."""
        if not self.pipelines:
            try:
                # Conditionally import transformers only when not testing
                from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

                for model_name in self.model_names:
                    logger.info(f"Loading NER model: {model_name}")
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    model = AutoModelForTokenClassification.from_pretrained(model_name)
                    self.pipelines.append(
                        pipeline(
                            "ner",
                            model=model,
                            tokenizer=tokenizer,
                            aggregation_strategy="simple",
                        )
                    )
                logger.info("All NER models loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load one or more NER models: {e}")
                self.pipelines = []

    def is_ready(self) -> bool:
        """Check if the NER models are loaded and ready."""
        return bool(self.pipelines)

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts named entities from the given text using the ensemble of models.
        """
        if not self.is_ready():
            logger.warning("NER models not available. Skipping entity extraction.")
            return []

        all_entities = []
        for nlp_pipeline in self.pipelines:
            try:
                entities = nlp_pipeline(text)
                all_entities.extend(entities)
            except Exception as e:
                logger.error(f"Error during NER processing with one of the models: {e}")

        return self._consolidate_entities(all_entities)

    def _consolidate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Consolidates entities from multiple models, preferring the one with the highest score
        for overlapping entities.
        """
        if not entities:
            return []

        # Simple consolidation: group by word and pick the highest score
        consolidated = {}
        for entity in entities:
            word = entity.get("word")
            if not word:
                continue

            if word not in consolidated or entity.get("score", 0) > consolidated[word].get("score", 0):
                consolidated[word] = entity

        return list(consolidated.values())