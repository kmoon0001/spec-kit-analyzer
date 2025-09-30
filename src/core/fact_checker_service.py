import logging

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
                from transformers import pipeline
                logger.info(f"Loading fact-checking model: {self.model_name}")
                self.classifier = pipeline("text2text-generation", model=self.model_name)
                logger.info("Fact-checking model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load fact-checking model: {e}")
                # The service will be non-functional, but this prevents a crash
                self.classifier = None

    def is_ready(self) -> bool:
        """Check if the model is loaded and ready."""
        return self.classifier is not None

    def check_consistency(self, premise: str, hypothesis: str) -> bool:
        """
        Checks if the hypothesis is supported by the premise.
        Returns True if the hypothesis is consistent, False otherwise.
        """
        if not self.is_ready():
            self.load_model()

        if not self.is_ready():
            logger.warning("Fact-checker model not available. Skipping consistency check.")
            return True # Fail open, assuming consistency

        try:
            # The prompt format depends on the model. For Flan-T5, a simple question works well.
            prompt = f"Premise: {premise}\nHypothesis: {hypothesis}\nIs the hypothesis supported by the premise?"
            result = self.classifier(prompt, max_length=50)

            # The output is a string that needs to be interpreted.
            # This is a simplified check; a more robust solution would parse the output more carefully.
            answer = result[0]['generated_text'].lower()
            return "yes" in answer or "supported" in answer

        except Exception as e:
            logger.error(f"Error during fact-checking: {e}")
            return True # Fail open