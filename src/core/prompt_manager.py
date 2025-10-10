import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages loading and formatting of prompt templates from the resources directory.
    """

    def __init__(self, template_name: str):
        """Initializes the PromptManager by loading a specific prompt template.

        Args:
            template_name: The filename of the prompt template in the prompts directory.

        """
        prompts_dir = os.path.join(
            os.path.dirname(__file__), "..", "resources", "prompts",
        )
        self.template_path = os.path.join(prompts_dir, template_name)
        self.template_string = self._load_template()

    def _load_template(self) -> str:
        """Loads the prompt template from the file system."""
        if not os.path.exists(self.template_path):
            logger.error("Prompt template not found: %s", self.template_path)
            raise FileNotFoundError(f"Prompt template not found: {self.template_path}")

        with open(self.template_path, encoding="utf-8") as f:
            return f.read()

    def get_prompt(self, **kwargs: Any) -> str:
        """Formats the loaded prompt template with the given keyword arguments.

        Args:
            **kwargs: The variables to substitute into the prompt template.

        Returns:
            The formatted prompt string.

        """
        try:
            return self.template_string.format(**kwargs)
        except KeyError as e:
            logger.exception(
                "Missing variable in prompt template %s: %s",
                self.template_path,
                e,
            )
            raise

    def build_prompt(self, **kwargs: Any) -> str:
        """Alias for get_prompt to maintain backward compatibility.

        Args:
            **kwargs: The variables to substitute into the prompt template.

        Returns:
            The formatted prompt string.

        """
        return self.get_prompt(**kwargs)
