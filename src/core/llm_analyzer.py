import json
import logging
from typing import Any

from .llm_service import LLMService
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class LLMComplianceAnalyzer:
    """Lightweight orchestrator for LLM-driven compliance analysis."""

    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager) -> None:
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager

    def analyze_document(self, document_text: str, context: str) -> dict[str, Any]:
        prompt = self.prompt_manager.get_prompt(
            document_text=document_text,
            context=context,
        )
        raw_response = self.llm_service.generate(prompt)
        return self._parse_response(raw_response)

    def _parse_response(self, raw_response: str) -> dict[str, Any]:
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            logger.error("LLM returned non-JSON payload: %s", raw_response)
            return {"raw_output": raw_response}
