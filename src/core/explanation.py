import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ExplanationEngine:
<<<<<<< HEAD
    """
    A service to post-process analysis findings, adding explanations and context.
    """
||||||| c46cdd8
    """
    A placeholder for the Explanation Engine.

    In a real implementation, this service would link analysis findings
    back to the specific text in the source document that triggered them.
    """
    def __init__(self, **kwargs):
        """
        Initializes the Explanation Engine.
        """
        logger.info("Initializing ExplanationEngine.")
        # No model loading needed for this placeholder.
=======
    """A service to post-process analysis findings, adding explanations and context."""

    def add_explanations(self, analysis_result: Dict[str, Any], full_document_text: str) -> Dict[str, Any]:
        """
        Adds explanations and context snippets to each finding.
>>>>>>> origin/main

<<<<<<< HEAD
    def add_explanations(self, analysis_result: Dict[str, Any], full_document_text: str) -> Dict[str, Any]:
        """
        Adds explanations and context snippets to each finding.
||||||| c46cdd8
    def add_explanations(self, analysis_result: Dict[str, Any], document_text: str) -> Dict[str, Any]:
        """
        Adds explanations to the analysis result.
=======
        Args:
            analysis_result: The raw analysis result from the LLM.
            full_document_text: The complete text of the document that was analyzed.
>>>>>>> origin/main

<<<<<<< HEAD
        Args:
            analysis_result: The raw analysis result from the LLM.
            full_document_text: The complete text of the document that was analyzed.

        Returns:
            The analysis result with added context.
||||||| c46cdd8
        This placeholder implementation simply passes the analysis through.
=======
        Returns:
            The analysis result with added context.
>>>>>>> origin/main
        """
        if "findings" not in analysis_result:
            return analysis_result

        for finding in analysis_result["findings"]:
            problematic_text = finding.get("text")
            if problematic_text:
                # Add a context snippet to help with precise highlighting
                finding['context_snippet'] = self._get_context_snippet(problematic_text, full_document_text)

        return analysis_result

    @staticmethod
    def _get_context_snippet(text_to_find: str, full_text: str, window: int = 20) -> str:
        """
        Finds a snippet of text and returns it with a surrounding context window.

        Args:
            text_to_find: The specific text of the finding.
            full_text: The entire document text.
            window: The number of characters to include on either side of the text.

        Returns:
            A snippet of text including the finding and its context.
        """
        try:
            start_index = full_text.find(text_to_find)
            if start_index == -1:
                return text_to_find # Return the original text if not found

            # Define the window boundaries
            context_start = max(0, start_index - window)
            context_end = min(len(full_text), start_index + len(text_to_find) + window)

            return full_text[context_start:context_end]
        except Exception:
            # If anything goes wrong, just fall back to the original text
            return text_to_find
