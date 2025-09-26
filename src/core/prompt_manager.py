import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

class PromptManager:
    """
    A service to load, manage, and format prompts from template files.
    """
    def __init__(self, template_path: str):
        """
        Initializes the Prompt Manager by loading a template from the given path.

        Args:
            template_path: The file path to the prompt template.
        """
        self.template_path = template_path
        self.template = ""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                self.template = f.read()
            logger.info(f"Successfully loaded prompt template from {template_path}")
        except FileNotFoundError:
            logger.error(f"Prompt template file not found at: {template_path}")
            # We allow it to fail gracefully, build_prompt will return an empty string.
        except Exception as e:
            logger.error(f"Error loading prompt template from {template_path}: {e}")

    def build_prompt(self, **kwargs: Any) -> str:
        """
        Builds a final prompt string by formatting the loaded template
        with the provided keyword arguments.

        Returns:
            The formatted prompt string, or an empty string if the template
            was not loaded successfully.
        """
        if not self.template:
            logger.error(f"Cannot build prompt; template from {self.template_path} is empty or was not loaded.")
            return ""

        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing key in prompt template '{self.template_path}': {e}")
            return "" # Return empty string on formatting error
        except Exception as e:
            logger.error(f"An unexpected error occurred during prompt building: {e}")
            return ""