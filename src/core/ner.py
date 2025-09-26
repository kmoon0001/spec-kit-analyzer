import logging
from transformers import (
    pipeline,
    AutoTokenizer,
    AutoModelForTokenClassification,
    PreTrainedModel,
    PreTrainedTokenizer,
)
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class NERPipeline:
    """
    A pipeline for Named Entity Recognition that uses an ensemble of models
    to achieve higher accuracy and recall.
    """
    def __init__(self, model_names: List[str]):
        """
        Initializes the NER ensemble by loading multiple models.

        Args:
            model_names: A list of model names from the Hugging Face Hub.
        """
        self.pipelines = []
        for model_name in model_names:
            try:
                logger.info(f"Loading NER model: {model_name}...")
                # Load model and tokenizer with explicit types to help mypy resolve overloads
                tokenizer: PreTrainedTokenizer = AutoTokenizer.from_pretrained(model_name)
                model: PreTrainedModel = AutoModelForTokenClassification.from_pretrained(model_name)
                # Create a pipeline for this model
                self.pipelines.append(
                    pipeline(  # type: ignore[call-overload]
                        "ner",
                        model=model,
                        tokenizer=tokenizer,
                        aggregation_strategy="simple",
                    )
                )
                logger.info(f"Successfully loaded NER model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load NER model {model_name}: {e}", exc_info=True)

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts entities from the text using the ensemble of models and merges the results.

        Args:
            text: The input text to analyze.

        Returns:
            A list of unique entities found by the ensemble.
        """
        if not self.pipelines:
            logger.warning("No NER models loaded. Cannot extract entities.")
            return []

        all_entities = set()

        for ner_pipeline in self.pipelines:
            try:
                entities = ner_pipeline(text)
                for entity in entities:
                    # Create a unique, hashable representation of the entity to avoid duplicates
                    entity_tuple = (
                        entity.get('entity_group'),
                        entity.get('word'),
                        entity.get('start'),
                        entity.get('end')
                    )
                    all_entities.add(entity_tuple)
            except Exception as e:
                logger.error(f"Error during entity extraction with one of the models: {e}", exc_info=True)

        # Convert the set of unique tuples back into a list of dictionaries
        unique_entity_list = [
            {
                "entity_group": group,
                "word": word,
                "start": start,
                "end": end
            }
            for group, word, start, end in all_entities
        ]

        logger.info(f"Extracted {len(unique_entity_list)} unique entities from ensemble.")
        return unique_entity_list
