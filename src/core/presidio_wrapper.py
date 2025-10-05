"""
Shared utilities for working with Presidio, including custom patterns.
"""
from __future__ import annotations

import logging

from presidio_analyzer import Pattern, PatternRecognizer
from presidio_anonymizer.entities import OperatorConfig

logger = logging.getLogger(__name__)

# Custom Presidio Recognizers for clinical-specific entities.
# These can be added to any RecognizerRegistry.
CUSTOM_RECOGNIZERS = (
    PatternRecognizer(
        supported_entity="MRN",
        name="medical_record_number_recognizer",
        patterns=[
            Pattern(name="mrn_alphanumeric", regex=r"\b(?:MRN[:\s-]*)?[A-Z0-9]{6,}\b", score=0.4),
        ],
    ),
    PatternRecognizer(
        supported_entity="ACCOUNT_NUMBER",
        name="account_number_recognizer",
        patterns=[
            Pattern(name="account_digits", regex=r"\b[A-Z]{0,3}\d{6,}\b", score=0.3),
        ],
    ),
)

def build_default_operators(replacement: str) -> dict[str, OperatorConfig]:
    """
    Helper to build a Presidio operator map for a given replacement token.

    Args:
        replacement: The string to use for replacing detected entities.

    Returns:
        A dictionary of operators for the Presidio AnonymizerEngine.
    """
    return {"DEFAULT": OperatorConfig("replace", {"new_value": replacement})}


__all__ = ["CUSTOM_RECOGNIZERS", "build_default_operators"]
