import logging
from typing import Dict, Any, List
import spacy

logger = logging.getLogger(__name__)

class ClinicalEntityService:
    """
    A service for extracting and normalizing clinical entities from text.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.normalization_map = self._load_normalization_map()
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model 'en_core_web_sm' not found. Defaulting to a simple NER.")
            self.nlp = None

    def _load_normalization_map(self) -> Dict[str, str]:
        """
        Loads a normalization map. In a real application, this would come
        from a more robust source like a database or a dedicated terminology service.
        """
        return {
            "pain": "Pain",
            "range of motion": "Range of Motion",
            "rom": "Range of Motion",
            "strength": "Strength",
            "gait": "Gait",
            "balance": "Balance",
            "ADLs": "Activities of Daily Living",
            "activities of daily living": "Activities of Daily Living",
        }

    def extract_and_normalize_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts clinical entities and normalizes them.
        """
        if not self.nlp:
            return []

        doc = self.nlp(text)
        entities = []
        for ent in doc.ents:
            normalized_term = self.normalization_map.get(ent.text.lower(), ent.text)
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start_char": ent.start_char,
                "end_char": ent.end_char,
                "normalized_term": normalized_term,
            })

        # Simple keyword matching as a fallback
        for term, normalized in self.normalization_map.items():
            if term in text.lower() and not any(e['normalized_term'] == normalized for e in entities):
                 entities.append({
                    "text": term,
                    "label": "CLINICAL_KEYWORD",
                    "start_char": -1, # Not from NER
                    "end_char": -1,   # Not from NER
                    "normalized_term": normalized,
                })

        return entities