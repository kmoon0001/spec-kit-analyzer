import logging

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

logger = logging.getLogger(__name__)


class PhiScrubberService:
    """
    A service for robustly scrubbing Protected Health Information using Presidio.
    """

    def __init__(self):
        """Initializes the Presidio-based PHI Scrubber Service."""
        logger.info("Initializing PhiScrubberService with Presidio.")
        # Setup the analyzer
        self.analyzer = AnalyzerEngine()
        # Setup the anonymizer
        self.anonymizer = AnonymizerEngine()
        logger.info("PhiScrubberService initialized.")

    def scrub(self, text: str) -> str:
        """
        Scrubs PHI from the provided text using Presidio.

        Args:
            text: The text to scrub.

        Returns:
            The scrubbed text.
        """
        if not isinstance(text, str) or not text.strip():
            return text

        try:
            # Analyze the text to find PII
            analyzer_results = self.analyzer.analyze(
                text=text,
                language="en",
            )

            # Anonymize the text, replacing all identified entities with a generic tag
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=analyzer_results,
                operators={"DEFAULT": OperatorConfig("replace", {"new_value": "<PHI>"})}
            )

            return anonymized_result.text
        except Exception as e:
            logger.error(f"Error scrubbing text with Presidio: {e}", exc_info=True)
            # Fallback to returning the original text if scrubbing fails
            return text