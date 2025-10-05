"""PHI scrubbing service built on Presidio with configuration support."""
from __future__ import annotations

import logging
from typing import Optional

from presidio_anonymizer.entities import OperatorConfig

from src.core.presidio_wrapper import (
    PresidioWrapper,
    build_default_operators,
    get_presidio_wrapper,
)

logger = logging.getLogger(__name__)


class PhiScrubberService:
    """A service for scrubbing Protected Health Information (PHI)."""

    def __init__(
        self,
        domain: str = "general",
        replacement: Optional[str] = None,
        wrapper: Optional[PresidioWrapper] = None,
        operators: Optional[dict[str, OperatorConfig]] = None,
    ) -> None:
        self.domain = domain
        configured_replacement, configured_model = self._resolve_configuration(domain)

        self.replacement = replacement or configured_replacement or "<PHI>"
        if wrapper is not None:
            self.wrapper = wrapper
        elif get_presidio_wrapper is not None:
            self.wrapper = get_presidio_wrapper(domain=domain, model_name=configured_model)
        else:
            self.wrapper = None
        self.operators = operators or build_default_operators(self.replacement)

    def _resolve_configuration(self, domain: str) -> tuple[Optional[str], Optional[str]]:
        try:
            from src.config import get_settings

            settings = get_settings()
        except Exception:  # noqa: BLE001 - defensive runtime safeguard
            return None, None

        models_cfg = getattr(settings, "models", None)
        if not models_cfg:
            return None, None

        scrubber_cfg = getattr(models_cfg, "phi_scrubber", None)
        if not scrubber_cfg:
            return None, None

        attr = "general_model" if domain == "general" else f"{domain}_model"
        model_name = getattr(scrubber_cfg, attr, None)
        return getattr(scrubber_cfg, "replacement_token", None), model_name

    def scrub(self, text: str):
        """Scrub PHI from the provided text."""
        if not isinstance(text, str) or not text.strip():
            return text

        if self.wrapper is None:
            logger.warning("Presidio wrapper unavailable; returning original text unmodified")
            return text

        try:
            analyzer_results = self.wrapper.analyze(text)
            anonymized = self.wrapper.anonymize(
                text=text, analyzer_results=analyzer_results, operators=self.operators
            )
            return getattr(anonymized, "text", anonymized)
        except Exception as exc:  # noqa: BLE001 - log and remain lossless
            logger.error("Error scrubbing text with Presidio: %s", exc, exc_info=True)
            return text


__all__ = ["PhiScrubberService"]
