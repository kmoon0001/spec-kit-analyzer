from spellchecker import SpellChecker

class PreprocessingService:
    """
    A service for cleaning and correcting text before analysis.
    """
    def __init__(self):
        self.spell = SpellChecker()

    def correct_text(self, text: str) -> str:
        """
        Corrects spelling mistakes in the given text.
        """
        words = text.split()
        corrected_words = [self.spell.correction(word) if self.spell.correction(word) is not None else word for word in words]
        return " ".join(corrected_words)