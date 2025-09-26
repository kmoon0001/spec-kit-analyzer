import logging
from spellchecker import SpellChecker

logger = logging.getLogger(__name__)

class PreprocessingService:
    """
    A service for cleaning and correcting text before analysis.
    """
    def __init__(self):
        """
        Initializes the PreprocessingService with a spell checker.
        """
        self.spell = SpellChecker()
        # You can add a domain-specific dictionary for better accuracy
        # self.spell.word_frequency.load_text_file('./medical_terms.txt')
        logger.info("PreprocessingService initialized with spell checker.")

    def correct_text(self, text: str) -> str:
        """
        Corrects spelling errors in the given text.
        """
        if not text:
            return ""

        words = text.split()
        # Find words that are misspelled
        misspelled = self.spell.unknown(words)

        corrected_words = []
        for word in words:
            # We correct the word only if it's in the misspelled set
            if word in misspelled:
                # Get the one `most likely` answer
                corrected_word = self.spell.correction(word)
                if corrected_word:
                    corrected_words.append(corrected_word)
                else:
                    corrected_words.append(word) # Keep original if no correction found
            else:
                corrected_words.append(word)

        corrected_text = " ".join(corrected_words)
        if misspelled:
            logger.debug(f"Performed spelling correction. Original: '{text}' -> Corrected: '{corrected_text}'")

        return corrected_text