import json
import logging
from typing import Any

import requests
from requests.exceptions import HTTPError
from transformers import pipeline

logger = logging.getLogger(__name__)


class FactCheckerService:
    """Check factual consistency using either a small NLI model or the main LLM.

    Backends:
    - pipeline: transformers text2text/classifier pipeline (default, lightweight)
    - llm: reuse the primary LLMService with an NLI-style prompt for yes/no
    """

    def __init__(
        self,
        model_name: str = "google/flan-t5-small",
        llm_service: Any | None = None,
        backend: str = "pipeline",
    ) -> None:
        self.model_name = model_name
        self.backend = (backend or "pipeline").lower()
        self.classifier = None
        self.llm_service = llm_service

    def load_model(self) -> None:
        """Lazy-load the NLI model when using the pipeline backend."""
        if self.backend != "pipeline":
            return
        if self.classifier is None:
            try:
                logger.info("Loading fact-checking model: %s", self.model_name)
                self.classifier = pipeline(
                    "text2text-generation", model=self.model_name
                )
                logger.info("Fact-checking model loaded successfully.")
            except (ValueError, TypeError, AttributeError) as e:
                logger.exception("Failed to load fact-checking model: %s", e)
                self.classifier = None

    def is_ready(self) -> bool:
        """Check if this service can run now."""
        if self.backend == "llm":
            return bool(self.llm_service) and bool(self.llm_service.is_ready())
        return self.classifier is not None

    def check_consistency(self, premise: str, hypothesis: str) -> bool:
        """Checks if the hypothesis is supported by the premise.
        Returns True if the hypothesis is consistent, False otherwise.
        """
        # Ensure backend is ready
        if self.backend == "pipeline":
            if not self.is_ready():
                self.load_model()
            if not self.is_ready():
                logger.warning(
                    "Fact-checker pipeline not available. Skipping consistency check."
                )
                return True  # Fail open, assuming consistency
        else:  # llm backend
            if not self.is_ready():
                logger.warning("LLM backend not ready for fact checking; failing open")
                return True

        try:
            if self.backend == "llm" and self.llm_service is not None:
                # Simple NLI-style instruction expecting yes/no
                nli_prompt = (
                    "You are a clinical compliance NLI checker.\n"
                    "Decide if the hypothesis is supported by the premise.\n"
                    "Answer strictly with 'YES' or 'NO'.\n\n"
                    f"Premise: {premise}\n"
                    f"Hypothesis: {hypothesis}\n"
                    "Answer:"
                )
                raw = self.llm_service.generate(nli_prompt, max_new_tokens=8, temperature=0.0)
                text = (raw or "").strip().lower()
                return text.startswith("yes")
            else:
                # Pipeline backend (e.g., flan-t5-small)
                prompt = (
                    f"Premise: {premise}\nHypothesis: {hypothesis}\n"
                    "Is the hypothesis supported by the premise?"
                )
                if self.classifier is None:
                    logger.error("Classifier is not loaded")
                    return True  # Fail open
                result = self.classifier(prompt, max_length=50)
                answer = (result[0].get("generated_text", "")).lower()
                return "yes" in answer or "supported" in answer

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.exception("Error during fact-checking: %s", e)
            return True  # Fail open

    def is_finding_plausible(self, finding: dict, rule: dict) -> bool:
        """Check if a finding is plausible given the associated rule.

        Args:
            finding: Dictionary containing finding details
            rule: Dictionary containing rule details

        Returns:
            True if the finding is plausible, False otherwise

        """
        try:
            # Extract relevant text from finding and rule
            finding_text = finding.get("problematic_text", "")
            rule_text = rule.get("content", "") or rule.get("regulation", "")

            if not finding_text or not rule_text:
                logger.warning("Missing text for fact-checking, assuming plausible")
                return True

            # Use the consistency checker to validate the finding against the rule
            return self.check_consistency(rule_text, finding_text)

        except (
            requests.RequestException,
            ConnectionError,
            TimeoutError,
            HTTPError,
        ) as e:
            logger.exception("Error checking finding plausibility: %s", e)
            return True  # Fail open
