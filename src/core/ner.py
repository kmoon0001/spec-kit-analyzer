import logging
from typing import List, Dict, Any
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

logger = logging.getLogger(__name__)

class NERPipeline:
    """
    A wrapper for a Hugging Face Named Entity Recognition pipeline.
    """
    def __init__(self, model_name: str, **kwargs):
        """
        Initializes the NER Pipeline by loading a model from Hugging Face.

        Args:
            model_name: The name of the Hugging Face model to use.
        """
        logger.info(f"Initializing NERPipeline with model: {model_name}")
        try:
            # Use Auto* classes for better compatibility
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForTokenClassification.from_pretrained(model_name)

            # aggregation_strategy="simple" groups sub-word tokens into whole words.
            self.pipeline = pipeline(
                "ner",
                model=model,
                tokenizer=tokenizer,
                aggregation_strategy="simple"
            )
            logger.info(f"Successfully initialized NER pipeline with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load NER model '{model_name}'. Error: {e}", exc_info=True)
            self.pipeline = None

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts named entities from the given text.

        Args:
            text: The text to analyze.

        Returns:
            A list of dictionaries, where each dictionary represents an entity.
            Returns an empty list if the pipeline failed to initialize.
        """
        if not self.pipeline:
            logger.error("NER pipeline is not available. Cannot extract entities.")
            return []

        try:
            entities = self.pipeline(text)
            # The pipeline returns numpy types, which are not JSON serializable.
            # We convert them to standard Python types.
            return [
                {
                    "entity_group": entity["entity_group"],
                    "score": float(entity["score"]),
                    "word": entity["word"],
                    "start": int(entity["start"]),
                    "end": int(entity["end"]),
                }
                for entity in entities
            ]
        except Exception as e:
            logger.error(f"An error occurred during entity extraction: {e}", exc_info=True)
            return []