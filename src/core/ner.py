import logging
import os
import spacy
from typing import List, Dict, Any
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

logger = logging.getLogger(__name__)

class NERPipeline:
    """
    A pipeline for Named Entity Recognition that uses an ensemble of models
    to achieve higher accuracy and recall.
    """

    def __init__(self, model_names: List[str]):
        """
        Initializes the NER ensemble.

        Args:
            model_names: A list of model names from the Hugging Face Hub.
        """
        self.pipelines = []
        self.spacy_nlp = spacy.load("en_core_web_sm")

        for model_name in model_names:
            try:
                logger.info(f"Loading NER model: {model_name}...")
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
                logger.info(f"Successfully loaded NER model: {model_name}")
            except Exception as e:
                logger.error(
                    f"Failed to load NER model {model_name}: {e}", exc_info=True
                )

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts entities from the text using the ensemble of models and merges the results.
        Placeholder implementation.
        """
        all_entities = []
        for pipe in self.pipelines:
            all_entities.extend(pipe(text))
        return all_entities

    def extract_clinician_name(self, text: str) -> List[str]:
        """
        Extracts clinician names from the text by looking for PERSON entities near keywords.
        """
        clinician_names = []
        doc = self.spacy_nlp(text)
        keywords = {"signature", "therapist", "by", "dr", "pt", "ot", "slp", "cota", "pta"}
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                # Check for keywords in the vicinity of the entity
                for token in doc[max(0, ent.start - 5) : min(len(doc), ent.end + 5)]:
                    if token.text.lower().strip(".:,") in keywords:
                        clinician_names.append(ent.text)
                        break
        return list(set(clinician_names))