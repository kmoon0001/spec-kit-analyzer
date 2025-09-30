import logging
import re
from typing import Dict

from spellchecker import SpellChecker

from ..config import get_settings

logger = logging.getLogger(__name__)


class PreprocessingService:
    """
    A high-performance service for cleaning and preparing text for analysis.

    This service features a robust, regex-based tokenizer, a cache for spelling
    corrections to boost performance, and loads a custom medical dictionary to
    improve accuracy for clinical text.
    """

    def __init__(self):
        """
        Initializes the service, loads the medical spell-checker, and sets up the cache.
        """
        self.settings = get_settings()
        self.spell = SpellChecker()
        # A simple in-memory cache to store corrections for common misspellings.
        self.correction_cache: Dict[str, str] = {}
        # A robust regex to split text while preserving punctuation and contractions.
        self.word_tokenizer = re.compile(r"\b\w+(?:['’]\w+)*\b|[.,;?!]")
        self._load_medical_dictionary()

    def _load_medical_dictionary(self):
        """
        Loads a custom medical dictionary from the path specified in the config.
        """
        try:
            # Get dictionary path from the centralized configuration.
            dict_path = self.settings.paths.medical_dictionary
            self.spell.word_frequency.load_text_file(dict_path)
            logger.info("Successfully loaded custom medical dictionary from: %s", dict_path)
        except FileNotFoundError:
            logger.error(
                "Medical dictionary not found at path: %s. "
                "Spell-checking accuracy will be reduced.",
                self.settings.paths.medical_dictionary,
            )
        except Exception as e:
            logger.error(
                "Failed to load custom medical dictionary: %s", e, exc_info=True
            )

    def correct_text(self, text: str) -> str:
        """
        Corrects spelling errors in the text using a cached, dictionary-aware approach.

        Args:
            text: The input string to be corrected.

        Returns:
            The corrected string.
        """
        if not isinstance(text, str) or not text.strip():
            return ""

        tokens = self.word_tokenizer.findall(text)
        if not tokens:
            return ""

        # Identify only the unknown words to minimize processing.
        unknown_words = self.spell.unknown(
            [word for word in tokens if word.isalpha()]
        )

        if not unknown_words:
            return text

        corrected_tokens = []
        corrected_count = 0
        for token in tokens:
            # Only attempt to correct alphabetic tokens that are unknown.
            if token in unknown_words:
                # Use the cache to avoid re-computing known corrections.
                if token not in self.correction_cache:
                    correction = self.spell.correction(token)
                    self.correction_cache[token] = (
                        correction if correction != token else token
                    )

                corrected_word = self.correction_cache[token]
                if corrected_word != token:
                    corrected_count += 1
                corrected_tokens.append(corrected_word)
            else:
                corrected_tokens.append(token)

        if corrected_count > 0:
            logger.info("Corrected %d misspelled words.", corrected_count)

        # Rejoin the tokens into a single string.
        return "".join(
            (
                " " + token if i > 0 and token.isalpha() else token
                for i, token in enumerate(corrected_tokens)
            )
        ).lstrip()