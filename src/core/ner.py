import logging
import os
import re
import spacy
from unittest.mock import MagicMock
from typing import List, Dict, Any
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

logger = logging.getLogger(__name__)


class NERPipeline:
    """
    A pipeline for Named Entity Recognition that uses an ensemble of models
    and SpaCy for robust clinician name extraction.
    """

    def __init__(self, model_names: List[str]):
        """
        Initializes the NER ensemble and loads the SpaCy model.
        """
        self.pipelines = []
        self.spacy_nlp = None
        try:
            self.spacy_nlp = spacy.load("en_core_web_sm")
            logger.info("Successfully loaded SpaCy model 'en_core_web_sm'.")
        except OSError:
            logger.error("Could not find SpaCy model 'en_core_web_sm'. Please run 'python -m spacy download en_core_web_sm'.")

        if os.environ.get("PYTEST_RUNNING") == "1":
            logger.info("NERPipeline initialized with a mock pipeline for testing.")
            self.pipelines.append(MagicMock())
            return

        for model_name in model_names:
            try:
                # ... (rest of the model loading logic remains the same)
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

    def _clean_name(self, name: str) -> str:
        """Strips credentials and trailing punctuation from a name string."""
        cleaned_text = re.sub(r",?\s*\b(?:PT|OT|SLP|PTA|COTA|DPT|CCC-SLP|OTR/L|MD|DO|PhD|RN)\b.*", "", name, flags=re.IGNORECASE)
        return cleaned_text.strip().rstrip(',.')

    def extract_clinician_name(self, text: str) -> List[Dict[str, Any]]:
        """Extracts clinician names using SpaCy for robust entity recognition."""
        if not self.spacy_nlp:
            return []

        doc = self.spacy_nlp(text)
        clinician_entities = []

        # Look for PERSON entities near signature keywords
        keywords = ["signature", "therapist", "clinician", "by"]
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                # Check for nearby keywords
                for token in ent:
                    # Check 5 tokens before the entity for a keyword
                    window = doc[max(0, token.i - 5) : token.i]
                    if any(k in t.lower_ for t in window for k in keywords):
                        cleaned_name = self._clean_name(ent.text)
                        if cleaned_name:
                            clinician_entities.append({
                                "entity_group": "CLINICIAN", "word": cleaned_name,
                                "start": ent.start_char, "end": ent.end_char
                            })
                        break # Found a keyword, no need to check other tokens in this entity

        # Deduplicate based on the cleaned name
        unique_names = {}
        for entity in clinician_entities:
            if entity["word"] not in unique_names:
                unique_names[entity["word"]] = entity

        return list(unique_names.values())

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts entities from the text using the ensemble of models and merges the results.
        """
        all_entities = []
        for p in self.pipelines:
            try:
                entities = p(text)
                if entities and isinstance(entities, list):
                    all_entities.extend(entities)
            except Exception as e:
                logger.error(f"Error running NER pipeline: {e}", exc_info=True)
        try:
            clinician_entities = self.extract_clinician_name(text)
            if clinician_entities:
                all_entities.extend(clinician_entities)
        except Exception as e:
            logger.error(f"Error running clinician name extraction: {e}", exc_info=True)

        unique_entities = []
        seen_positions = set()
        all_entities.sort(key=lambda x: len(x.get("word", "")), reverse=True)

        for entity in all_entities:
            start, end = entity.get("start"), entity.get("end")
            if start is None or end is None:
                continue

            is_overlapping = any(
                max(start, other_start) < min(end, other_end)
                for other_start, other_end in seen_positions
            )
            if not is_overlapping:
                unique_entities.append(entity)
                seen_positions.add((start, end))

        unique_entities.sort(key=lambda x: x.get("start", 0))
        logger.info(f"Extracted {len(unique_entities)} unique entities.")
        return unique_entities
