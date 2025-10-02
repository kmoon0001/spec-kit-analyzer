import logging
import spacy
from typing import List, Dict, Any
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

logger = logging.getLogger(__name__)

CLINICIAN_KEYWORDS = [
    "signature", "therapist", "co-signed by", "signed by", "provider", "clinician"
]
CLINICIAN_NER_LABELS = {"PERSON"}


class NERPipeline:
    """
    A pipeline for Named Entity Recognition that uses an ensemble of models
    to achieve higher accuracy and recall.
    """

    def __init__(self, model_names: List[str] = None):
        """
        Initializes the NER ensemble.

        Args:
            model_names: A list of model names from the Hugging Face Hub.
        """
        self.pipelines = []
        try:
            self.spacy_nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("en_core_web_sm not found, downloading...")
            spacy.cli.download("en_core_web_sm")
            self.spacy_nlp = spacy.load("en_core_web_sm")

        if model_names:
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
        (This is a placeholder for a more complex implementation)
        """
        if not self.pipelines:
            return []
        # For now, just use the first pipeline as a simple example
        return self.pipelines[0](text)


    def extract_clinician_name(self, text: str) -> List[str]:
        """
        Extracts clinician names from the text, prioritizing entities near clinician keywords.
        """
        if not text:
            return []

        doc = self.spacy_nlp(text)
        clinicians = set()

        # Find all person entities
        person_entities = [ent for ent in doc.ents if ent.label_ in CLINICIAN_NER_LABELS]

        # Check for proximity to keywords
        for person_ent in person_entities:
            # Look for keywords within a window around the person entity
            start_char = max(0, person_ent.start_char - 50) # 50 characters before
            end_char = min(len(text), person_ent.end_char + 50) # 50 characters after
            context = text[start_char:end_char].lower()

            for keyword in CLINICIAN_KEYWORDS:
                if keyword in context:
                    clinicians.add(person_ent.text)
                    break

        return sorted(list(clinicians))