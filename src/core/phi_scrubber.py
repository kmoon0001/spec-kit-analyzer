import re
import spacy
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class PhiScrubberService:
    """A service for detecting and redacting Protected Health Information (PHI)."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the PhiScrubberService with a configuration.

        Args:
            config (Dict[str, Any]): Configuration dictionary.
                Expected keys:
                - 'redaction_style': 'label' or 'placeholder'.
                - 'ner_labels': List of spaCy entity labels to redact.
                - 'regex_patterns': List of custom regex patterns.
        """
        self.config = config
        self.redaction_style = self.config.get("redaction_style", "label")
        self.ner_labels = self.config.get("ner_labels", ["PERSON", "DATE", "GPE", "ORG"])
        self.regex_patterns = self.config.get("regex_patterns", self._default_regex_patterns())

        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model 'en_core_web_sm' not found. Attempting to download.")
            from spacy.cli import download
            download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

    def _default_regex_patterns(self) -> List[Tuple[str, str]]:
        """Provides default regex patterns for PHI."""
        return [
            (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]"),
            (r"(\+?\d{1,2}[\s\-.]?)?(\(?\d{3}\)?[ \-.]?\d{3}[\-.]?\d{4})", "[PHONE]"),
            (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
            (r"\bMRN[:\s]*[A-Za-z0-9\-]{4,}\b", "[MRN]"),
        ]

    def scrub_text(self, text: str) -> str:
        """
        Scrub PHI from text using a hybrid approach (regex then NER).
        """
        if not isinstance(text, str):
            return text

        # First, use regex for specific, structured patterns.
        regex_scrubbed_text = self._scrub_with_regex(text)

        # Then, use NER for broader categories.
        final_scrubbed_text = self._scrub_with_ner(regex_scrubbed_text)

        return final_scrubbed_text

    def _scrub_with_regex(self, text: str) -> str:
        """Scrub PHI using configured regular expressions."""
        for pattern, replacement in self.regex_patterns:
            if self.redaction_style == 'placeholder':
                replacement = "[REDACTED]"
            text = re.sub(pattern, replacement, text)
        return text

    def _scrub_with_ner(self, text: str) -> str:
        """Scrub PHI using a Named Entity Recognition (NER) model."""
        doc = self.nlp(text)
        new_text_parts = []
        last_end = 0

        for ent in doc.ents:
            if ent.label_ in self.ner_labels:
                new_text_parts.append(text[last_end:ent.start_char])
                if self.redaction_style == 'label':
                    new_text_parts.append(f"[{ent.label_}]")
                else:
                    new_text_parts.append("[REDACTED]")
                last_end = ent.end_char

        new_text_parts.append(text[last_end:])
        return "".join(new_text_parts)

# For backward compatibility and simple use cases, a default instance can be provided.
default_scrubber = PhiScrubberService(config={})
scrub_phi = default_scrubber.scrub_text