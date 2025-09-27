import logging
import os
from spellchecker import SpellChecker

logger = logging.getLogger(__name__)

# Get the absolute path to the project's root directory
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class PreprocessingService:
    """
    A service for cleaning and preparing text before analysis.
    """
    def __init__(self):
        """
        Initializes the service and loads the medical spell-checker.
        """
        self.spell = SpellChecker()
        self._load_medical_dictionary()

    def _load_medical_dictionary(self):
        """
        Loads a custom medical dictionary to improve spell-checking accuracy.
        """
        try:
            dict_path = os.path.join(ROOT_DIR, "src", "resources", "medical_dictionary.txt")
            self.spell.word_frequency.load_text_file(dict_path)
            logger.info(f"Successfully loaded custom medical dictionary from {dict_path}")
        except Exception as e:
            logger.error(f"Failed to load custom medical dictionary: {e}")

    def correct_text(self, text: str) -> str:
        """
        Corrects spelling errors in the provided text using the custom dictionary.

        Args:
            text: The input string to be corrected.

        Returns:
            The corrected string.
        """
        if not text:
            return ""

        # Find the words that are misspelled
        misspelled = self.spell.unknown(text.split())

        if not misspelled:
            return text

        corrected_text = []
        for word in text.split():
            if word in misspelled:
                # Get the one `most likely` answer
                corrected_word = self.spell.correction(word)
                corrected_text.append(corrected_word)
            else:
                corrected_text.append(word)
        
        logger.info(f"Corrected {len(misspelled)} misspelled words.")
        return " ".join(corrected_text)
