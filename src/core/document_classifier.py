import logging

from .llm_service import LLMService
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class DocumentClassifier:
    """A service to classify a document into a predefined category."""

    def __init__(
        self,
        llm_service: LLMService,
        prompt_template_path: str | None = None,
        prompt_manager: PromptManager | None = None,
    ):
        """Initializes the classifier with optional prompt overrides."""
        import os

        self.llm_service = llm_service
        if prompt_manager is not None:
            self.prompt_manager = prompt_manager
        else:
            template_path = prompt_template_path or ""
            if not template_path:
                try:
                    from src.config import get_settings

                    template_path = get_settings().models.doc_classifier_prompt
                except (PermissionError, ImportError, FileNotFoundError, ModuleNotFoundError, OSError):
                    template_path = "src/resources/prompts/doc_classifier_prompt.txt"
            template_name = (
                os.path.basename(template_path) or os.path.basename(template_path.rstrip(os.sep)) or template_path
            )
            self.prompt_manager = PromptManager(template_name=template_name)
        self.possible_types = [
            "Progress Note",
            "Evaluation",
            "Discharge Summary",
            "Unknown",
        ]

    def classify_document(self, document_text: str) -> str:
        """Classifies the document text into one of the possible types.

        Args:
            document_text: The full text of the document to classify.

        Returns:
            A string representing the document type.

        """
        if not self.llm_service.is_ready():
            logger.warning("LLM not available, returning 'Unknown' document type.")
            return "Unknown"

        try:
            # To speed up classification on CPU, use a smaller snippet
            text_snippet = document_text[:800]

            prompt = self.prompt_manager.build_prompt(document_text=text_snippet)

            # Generate the classification using the LLM
            raw_classification = self.llm_service.generate(prompt)

            # Clean up the output
            classification = (raw_classification or "").strip().replace('"', "")

            # Ensure the classification is one of the valid types
            if classification in self.possible_types:
                logger.info("Document classified as: %s", classification)
                return classification
            logger.warning("LLM returned an unexpected document type: '%s'. Defaulting to 'Unknown'.", classification)
            return "Unknown"

        except Exception as e:
            logger.exception("Error during document classification: %s", e)
            return "Unknown"
