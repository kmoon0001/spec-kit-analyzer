"""Utilities for working with Presidio analyzers/anonymizers in a reusable way."""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

from presidio_analyzer import (
    AnalyzerEngine,
    Pattern,
    PatternRecognizer,
    RecognizerRegistry,
)
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

logger = logging.getLogger(__name__)


# Default transformer back-ends used if none are provided in configuration.
_DEFAULT_DOMAIN_MODELS = {
    "general": None,
    "biomedical": "emilyalsentzer/Bio_ClinicalBERT",
}


_CUSTOM_PATTERNS = (
    PatternRecognizer(
        supported_entity="MRN",
        name="medical_record_number",
        patterns=(
            Pattern("mrn_alphanumeric", r"\b(?:MRN[:\s-]*)?[A-Z0-9]{6,}\b", 0.4),
        ),
    ),
    PatternRecognizer(
        supported_entity="ACCOUNT_NUMBER",
        name="account_number",
        patterns=(
            Pattern("account_digits", r"\b[A-Z]{0,3}\d{6,}\b", 0.3),
        ),
    ),
)


class PresidioWrapper:
    """Lightweight wrapper that centralises Presidio configuration."""

    def __init__(self, transformer_model: Optional[str] = None, language: str = "en"):
        self.language = language
        self.transformer_model = transformer_model
        self.anonymizer = AnonymizerEngine()
        self.analyzer = self._create_analyzer()

    def _create_analyzer(self) -> AnalyzerEngine:
        provider = NlpEngineProvider()
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers()
        for recognizer in _CUSTOM_PATTERNS:
            registry.add_recognizer(recognizer)

        nlp_engine = None
        if self.transformer_model:
            config = {
                "nlp_engine_name": "transformers",
                "models": [
                    {
                        "lang_code": self.language,
                        "transformers_model": self.transformer_model,
                    }
                ],
            }
            try:
                nlp_engine = provider.create_engine(config)
            except Exception as exc:  # noqa: BLE001 - defensive fallback
                logger.warning(
                    "Falling back to rule-based Presidio analyzer: %s", exc
                )
                nlp_engine = None

        return AnalyzerEngine(
            registry=registry,
            nlp_engine=nlp_engine,
            supported_languages=[self.language],
        )

    def analyze(self, text: str):
        """Run Presidio analysis for the supplied text."""
        return self.analyzer.analyze(text=text, language=self.language)

    def anonymize(self, text: str, analyzer_results, operators):
        """Apply anonymisation, delegating to Presidio."""
        return self.anonymizer.anonymize(
            text=text, analyzer_results=analyzer_results, operators=operators
        )


@lru_cache(maxsize=8)
def get_presidio_wrapper(domain: str = "general", model_name: Optional[str] = None) -> PresidioWrapper:
    """Return a cached PresidioWrapper for the requested domain."""
    resolved_model = model_name or _DEFAULT_DOMAIN_MODELS.get(domain)
    return PresidioWrapper(transformer_model=resolved_model)


def build_default_operators(replacement: str) -> dict[str, OperatorConfig]:
    """Helper to build a Presidio operator map for a given replacement token."""
    return {"DEFAULT": OperatorConfig("replace", {"new_value": replacement})}


__all__ = ["PresidioWrapper", "get_presidio_wrapper", "build_default_operators"]
