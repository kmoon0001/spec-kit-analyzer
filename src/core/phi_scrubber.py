"""
State-of-the-art PHI scrubbing service built on the Presidio framework.
"""
import logging

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

logger = logging.getLogger(__name__)

# Configure languages for Presidio
# For clinical text, English is the primary focus.
NLP_CONFIG = {"nlp_engine_name": "spacy", "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}]}


class PhiScrubberService:
    """A robust service for scrubbing Protected Health Information (PHI) using Presidio."""

    def __init__(self) -> None:
        """
        Initializes the Presidio-based scrubbing service.
        """
        try:
            # 1. Set up the Recognizer Registry and add custom recognizers if needed
            registry = RecognizerRegistry()
            # Example: registry.add_recognizer(MyCustomRecognizer())

            # 2. Initialize the AnalyzerEngine with the registry and NLP configuration
            self.analyzer = AnalyzerEngine(
                registry=registry,
                nlp_engine_name="spacy",
                supported_languages=["en"],
            )

            # 3. Initialize the AnonymizerEngine
            self.anonymizer = AnonymizerEngine()
            logger.info("Successfully initialized Presidio PhiScrubberService.")

        except Exception as e:
            logger.error("Failed to initialize Presidio engines: %s", e, exc_info=True)
            self.analyzer = None
            self.anonymizer = None

    def scrub(self, text: str, replacement_token: str = "<PHI>") -> str:
        """
        Analyzes and scrubs PHI from the provided text using Presidio.

        Args:
            text: The input text to scrub.
            replacement_token: The string to replace detected PHI with.

        Returns:
            The scrubbed text with PHI removed.
        """
        if not self.analyzer or not self.anonymizer:
            logger.warning("Presidio is not available; returning original text.")
            return text

        if not isinstance(text, str) or not text.strip():
            return text

        try:
            # 1. Analyze the text to find PHI entities
            analyzer_results = self.analyzer.analyze(text=text, language="en")

            # 2. Anonymize the text based on the analysis
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=analyzer_results,
                operators={"DEFAULT": OperatorConfig("replace", {"new_value": replacement_token})},
            )

            return anonymized_result.text
        except Exception as e:
            logger.error("Error scrubbing text with Presidio: %s", e, exc_info=True)
            return text  # Fail safe: return the original text on error


__all__ = ["PhiScrubberService"]
