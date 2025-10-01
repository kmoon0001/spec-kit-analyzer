import logging
import re
from typing import List, Tuple, Set
from threading import Lock

import spacy
from spacy.language import Language

logger = logging.getLogger(__name__)

# --- Configuration for PHI Scrubbing ---

GENERAL_PHI_NER_LABELS: Set[str] = {"PERSON", "DATE", "GPE", "LOC", "ORG"}
BIOMEDICAL_PHI_NER_LABELS: Set[str] = {
    "PATIENT", "HOSPITAL", "DOCTOR", "AGE", "ID", "PHONE", "EMAIL", "URL",
    "STREET", "CITY", "STATE", "ZIP", "COUNTRY",
}
DEFAULT_REGEX_PATTERNS: List[Tuple[str, str]] = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
    (r"\b(MRN|mrn|medical record number)[\s:]*[A-Za-z0-9\-]{4,}\b", "[MRN]"),
    (r"(\+?\d{1,2}[\s\-.]?)?(\(?\d{3}\)?[ \-.]?\d{3}[\-.]?\d{4})", "[PHONE]"),
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]"),
    (r"\b\d{1,4}[-/]\d{1,2}[-/]\d{1,4}\b", "[DATE]"),
    (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[IP_ADDRESS]"),
    (r"\b[A-Z]{2}\d{8,}\b", "[ACCOUNT_NUMBER]"),
    # Add a pattern for common hospital names that NER might miss
    (r"\b\w+\s+(?:Hospital|Medical Center|Clinic)\b", "[HOSPITAL]"),
]


class PhiScrubberService:
    """
    A thread-safe, multi-model service for robustly scrubbing Protected Health Information.
    It uses a sophisticated single-pass replacement strategy:
    1. Collects all potential PHI spans from regex, a biomedical NER model, and a general NER model.
    2. Resolves any overlapping spans.
    3. Performs a single replacement pass on the original text.
    """
    _general_nlp: Language | None = None
    _biomed_nlp: Language | None = None
    _lock = Lock()

    def __init__(self):
        from ..config import get_settings
        settings = get_settings()
        self.general_model_name = settings.models.phi_scrubber.general
        self.biomed_model_name = settings.models.phi_scrubber.biomedical
        self.is_loading = False

    def _load_models(self):
        if self._general_nlp and self._biomed_nlp:
            return
        self.is_loading = True
        try:
            logger.info("Loading spaCy models for PHI scrubbing...")
            # Load to temp vars first for atomicity
            general_nlp = spacy.load(self.general_model_name)
            biomed_nlp = spacy.load(self.biomed_model_name)

            # Assign only after both are loaded successfully
            self._general_nlp = general_nlp
            self._biomed_nlp = biomed_nlp
            logger.info("All PHI scrubbing models loaded.")
        except OSError as e:
            logger.critical("Could not load a required spaCy model: %s", e, exc_info=True)
            self._general_nlp, self._biomed_nlp = None, None
        finally:
            self.is_loading = False

    def _ensure_models_loaded(self):
        if (self._general_nlp and self._biomed_nlp) or self.is_loading:
            return
        with self._lock:
            if not (self._general_nlp and self._biomed_nlp):
                self._load_models()

    def _get_spans_from_text(self, text: str) -> List[Tuple[int, int, str]]:
        spans = []
        # Get spans from regex
        for pattern, tag in DEFAULT_REGEX_PATTERNS:
            for match in re.finditer(pattern, text):
                spans.append((match.start(), match.end(), tag))

        # Get spans from biomedical NER
        if self._biomed_nlp:
            for ent in self._biomed_nlp(text).ents:
                if ent.label_ in BIOMEDICAL_PHI_NER_LABELS:
                    spans.append((ent.start_char, ent.end_char, f"[{ent.label_}]"))

        # Get spans from general NER
        if self._general_nlp:
            for ent in self._general_nlp(text).ents:
                if ent.label_ in GENERAL_PHI_NER_LABELS:
                    spans.append((ent.start_char, ent.end_char, f"[{ent.label_}]"))

        return spans

    def scrub(self, text: str) -> str:
        if not isinstance(text, str) or not text.strip():
            return text
        self._ensure_models_loaded()

        spans = self._get_spans_from_text(text)
        if not spans:
            return text

        # Sort spans by start index, then by longest span first to prioritize larger entities
        spans.sort(key=lambda s: (s[0], s[0] - s[1]))

        # Resolve overlaps by keeping the first one in the sorted list (which is the longest)
        resolved_spans = []
        last_end = -1
        for start, end, tag in spans:
            if start >= last_end:
                resolved_spans.append((start, end, tag))
                last_end = end

        # Build the new string with a single pass
        new_text_parts = []
        last_end = 0
        for start, end, tag in resolved_spans:
            new_text_parts.append(text[last_end:start])
            new_text_parts.append(tag)
            last_end = end
        new_text_parts.append(text[last_end:])

        return "".join(new_text_parts)