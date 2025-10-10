
"""
State-of-the-art PHI scrubbing service built on the Presidio framework.
"""
import logging

try:
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
except ImportError:  # pragma: no cover - optional dependency
    AnalyzerEngine = None  # type: ignore
    RecognizerRegistry = None  # type: ignore
    AnonymizerEngine = None  # type: ignore
    OperatorConfig = None  # type: ignore

logger = logging.getLogger(__name__)


class PhiScrubberService:
    """A robust service for scrubbing Protected Health Information (PHI)."""

    def __init__(
        self,
        replacement: str = "<PHI>",
        wrapper: object | None = None,
        analyzer: AnalyzerEngine | None = None,
        anonymizer: AnonymizerEngine | None = None,
    ) -> None:
        """Initialise Presidio-based scrubbing service with injectable components."""
        self.default_replacement = replacement

        self._custom_wrapper = False
        if wrapper is not None:
            self.analyzer = wrapper
            self.anonymizer = wrapper
            self._custom_wrapper = True
            return

        registry = None
        if analyzer is None and RecognizerRegistry is not None:
            try:
                registry = RecognizerRegistry()
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to initialize Presidio recognizer registry: %s", exc)
        if analyzer is None and AnalyzerEngine is not None:
            try:
                analyzer = AnalyzerEngine(
                    registry=registry if registry is not None else RecognizerRegistry(),
                    supported_languages=["en"],
                )
            except Exception as exc:
                logger.error("Failed to initialize Presidio AnalyzerEngine: %s", exc)
                analyzer = None
        if anonymizer is None and AnonymizerEngine is not None:
            try:
                anonymizer = AnonymizerEngine()
            except Exception as exc:
                logger.error("Failed to initialize Presidio AnonymizerEngine: %s", exc)
                anonymizer = None

        self.analyzer = analyzer
        self.anonymizer = anonymizer

    def scrub(self, text: str, replacement_token: str | None = None) -> str:
        """Analyze and scrub PHI from text using Presidio components."""
        if not isinstance(text, str) or not text.strip():
            return text

        if not self.analyzer or not self.anonymizer or OperatorConfig is None:
            logger.warning("Presidio is not available; returning original text.")
            return text

        token = replacement_token or self.default_replacement

        try:
            if not self.analyzer or not self.anonymizer:
                logger.warning("Analyzer or anonymizer not available, returning original text")
                return text

            if self._custom_wrapper:
                analyzer_results = self.analyzer.analyze(text)  # type: ignore[attr-defined]
            else:
                analyzer_results = self.analyzer.analyze(text=text, language="en")  # type: ignore[attr-defined]
            anonymized_result = self.anonymizer.anonymize(  # type: ignore[attr-defined]
                text=text,
                analyzer_results=analyzer_results,
                operators={"DEFAULT": OperatorConfig("replace", {"new_value": token})},
            )
            return anonymized_result.text
        except Exception as exc:
            logger.error("Error scrubbing text with Presidio: %s", exc, exc_info=True)
            return text


__all__ = ["PhiScrubberService"]
