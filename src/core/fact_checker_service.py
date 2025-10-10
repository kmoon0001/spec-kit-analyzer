import logging

from transformers import pipeline

logger = logging.getLogger(__name__)


class FactCheckerService:
    """A service to check for factual consistency using a Natural Language Inference model."""

    def __init__(self, model_name: str = "google/flan-t5-base"):
        self.model_name = model_name
        self.classifier = None

    def load_model(self):
        """Lazy-loads the NLI model."""
        if self.classifier is None:
            try:
                logger.info("Loading fact-checking model: %s", self.model_name)
                self.classifier = pipeline(
                    "text2text-generation", model=self.model_name,
                )
                logger.info("Fact-checking model loaded successfully.")
            except (ValueError, TypeError, AttributeError) as e:
                logger.exception("Failed to load fact-checking model: %s", e)
                # The service will be non-functional, but this prevents a crash
                self.classifier = None

    def is_ready(self) -> bool:
        """Check if the model is loaded and ready."""
        return self.classifier is not None

    def check_consistency(self, premise: str, hypothesis: str) -> bool:
        """Checks if the hypothesis is supported by the premise.
        Returns True if the hypothesis is consistent, False otherwise.
        """
        if not self.is_ready():
            self.load_model()

        if not self.is_ready():
            logger.warning(
                "Fact-checker model not available. Skipping consistency check.",
            )
            return True  # Fail open, assuming consistency

        try:
            # The prompt format depends on the model. For Flan-T5, a simple question works well.
            prompt = f"Premise: {premise}\nHypothesis: {hypothesis}\nIs the hypothesis supported by the premise?"
            if self.classifier is None:
                logger.error("Classifier is not loaded")
                return True  # Fail open
            result = self.classifier(prompt, max_length=50)

            # The output is a string that needs to be interpreted.
            # This is a simplified check; a more robust solution would parse the output more carefully.
            answer = result[0]["generated_text"].lower()
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

        except (requests.RequestException, ConnectionError, TimeoutError, HTTPError) as e:
            logger.exception("Error checking finding plausibility: %s", e)
            return True  # Fail open
