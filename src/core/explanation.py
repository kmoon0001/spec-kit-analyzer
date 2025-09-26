import logging
import random
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ExplanationEngine:
    """A service to post-process analysis findings, adding explanations and context."""

    def add_explanations(self, analysis_result: Dict[str, Any], full_document_text: str) -> Dict[str, Any]:
        """Adds context snippets and placeholder confidence scores to each finding."""
        if "findings" not in analysis_result or not isinstance(analysis_result.get("findings"), list):
            return analysis_result

        for finding in analysis_result["findings"]:
            # 1. Add a context snippet (from origin/main)
            problematic_text = finding.get("text")
            if problematic_text:
                finding['context_snippet'] = self._get_context_snippet(problematic_text, full_document_text)

            # 2. Add a dummy confidence score (from bugfix branch)
            if "confidence" not in finding:
                finding["confidence"] = round(random.uniform(0.85, 0.98), 2)

        return analysis_result

    @staticmethod
    def _get_context_snippet(text_to_find: str, full_text: str, window: int = 20) -> str:
        """
        Finds a snippet of text and returns it with a surrounding context window.
        """
        try:
            start_index = full_text.find(text_to_find)
            if start_index == -1:
                return text_to_find # Return the original text if not found

            context_start = max(0, start_index - window)
            context_end = min(len(full_text), start_index + len(text_to_find) + window)

            return full_text[context_start:context_end]
        except Exception:
            return text_to_find