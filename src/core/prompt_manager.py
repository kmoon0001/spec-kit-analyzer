import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

class PromptManager:
    def __init__(self, template_path: str):
        self.template_path = template_path
        self.template = ""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                self.template = f.read()
            logger.info(f"Successfully loaded prompt template from {template_path}")
        except FileNotFoundError:
            logger.error(f"Prompt template file not found at: {template_path}")
        except Exception as e:
            logger.error(f"Error loading prompt template from {template_path}: {e}")

    def build_prompt(self, **kwargs: Any) -> str:
        if not self.template:
            logger.error(f"Cannot build prompt; template from {self.template_path} is empty or was not loaded.")
            return ""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing key in prompt template '{self.template_path}': {e}")
            return ""
        except Exception as e:
            logger.error(f"An unexpected error occurred during prompt building: {e}")
            return ""