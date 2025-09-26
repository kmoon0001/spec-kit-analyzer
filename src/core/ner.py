import logging
import os
from unittest.mock import MagicMock
from typing import List, Dict, Any

# Conditionally import transformers only when not testing
if os.environ.get("PYTEST_RUNNING") != "1":
    from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

logger = logging.getLogger(__name__)

class NERPipeline:
    """
<<<<<<< HEAD
    A pipeline for Named Entity Recognition (NER) that can use an ensemble of models.
    It normalizes and combines results from multiple NER models.
||||||| c46cdd8
    A placeholder for the Named Entity Recognition pipeline.

    In a real implementation, this would use a library like spaCy or Hugging Face
    Transformers to extract medical entities from the text.
=======
    A pipeline for Named Entity Recognition that uses an ensemble of models
    to achieve higher accuracy and recall.
>>>>>>> origin/main
    """
    def __init__(self, model_names: List[str]):
        """
        Initializes the NER ensemble. If 'PYTEST_RUNNING' is set, it uses mock pipelines.

        Args:
            model_names: A list of model names from the Hugging Face Hub.
        """
<<<<<<< HEAD
        self.pipelines = []

        # Check for pytest environment to mock the model loading
        if os.environ.get("PYTEST_RUNNING") == "1":
            logger.info("NERPipeline initialized with a mock pipeline for testing.")
            # Create a mock pipeline that returns a predefined entity structure
            mock_pipeline = MagicMock()
            mock_pipeline.return_value = [
                {
                    'entity_group': 'test_entity',
                    'word': 'test',
                    'start': 10,
                    'end': 14
                }
            ]
            self.pipelines.append(mock_pipeline)
            return

        for model_name in model_names:
            try:
                logger.info(f"Loading NER model: {model_name}...")
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForTokenClassification.from_pretrained(model_name)
                self.pipelines.append(pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple"))
            except Exception as e:
                logger.error(f"Failed to load NER model {model_name}: {e}", exc_info=True)

        if not self.pipelines:
            logger.warning("No NER models were loaded. The NER pipeline will be non-functional.")
||||||| c46cdd8
        logger.info(f"Initializing NERPipeline with model: {model_name}")
        # In a real implementation, this would load a model.
        self.model = None
=======
        self.pipelines = []

        # Check for pytest environment to mock the model loading
        if os.environ.get("PYTEST_RUNNING") == "1":
            logger.info("NERPipeline initialized with a mock pipeline for testing.")
            # Create a mock pipeline that returns a predefined entity structure
            mock_pipeline = MagicMock()
            mock_pipeline.return_value = [
                {
                    'entity_group': 'test_entity',
                    'word': 'test',
                    'start': 10,
                    'end': 14
                }
            ]
            self.pipelines.append(mock_pipeline)
            return

        for model_name in model_names:
            try:
                logger.info(f"Loading NER model: {model_name}...")
                # Load model and tokenizer
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForTokenClassification.from_pretrained(model_name)
                # Create a pipeline for this model
                self.pipelines.append(pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple"))
                logger.info(f"Successfully loaded NER model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load NER model {model_name}: {e}", exc_info=True)
>>>>>>> origin/main

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
<<<<<<< HEAD
        Extracts entities from the text using the ensemble of NER models.
||||||| c46cdd8
        Extracts entities from the given text.

        Returns a list of placeholder entities.
=======
        Extracts entities from the text using the ensemble of models and merges the results.

        Args:
            text: The input text to analyze.

        Returns:
            A list of unique entities found by the ensemble.
>>>>>>> origin/main
        """
<<<<<<< HEAD
        if not self.pipelines:
            return []

        all_entities = []
        for p in self.pipelines:
            try:
                entities = p(text)
                all_entities.extend(entities)
            except Exception as e:
                logger.error(f"Error during NER prediction: {e}", exc_info=True)

        return self._consolidate_entities(all_entities)

    @staticmethod
    def _consolidate_entities(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Consolidates entities from multiple models, removing duplicates.
        """
        unique_entities = {}
        for entity in entities:
            key = (entity['entity_group'], entity['word'], entity['start'], entity['end'])
            if key not in unique_entities:
                unique_entities[key] = entity

        unique_entity_list = list(unique_entities.values())
        unique_entity_list.sort(key=lambda x: x['start'])

        logger.info(f"Extracted {len(unique_entity_list)} unique entities from ensemble.")
        return unique_entity_list
||||||| c46cdd8
        logger.info("Extracting entities (placeholder implementation).")
        # Return a fixed, dummy entity for testing purposes
        return [
            {"entity_group": "Condition", "word": "pain", "start": 10, "end": 14}
        ]
=======
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
>>>>>>> origin/main
