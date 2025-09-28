import logging
from typing import Dict, List

from .llm_service import LLMService
from .text_utils import sanitize_human_text

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "You are ClinicalCamel, a concise clinical compliance assistant."
    " Respond in English using plain ASCII characters."
    " Provide practical, regulation-aligned guidance for occupational, physical,"
    " and speech therapy documentation."
)


class ChatService:
    """Lightweight conversational wrapper around an LLM service."""

    def __init__(self, llm_service: LLMService, system_prompt: str | None = None) -> None:
        self.llm_service = llm_service
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

    def process_message(self, history: List[Dict[str, str]]) -> str:
        if not self.llm_service.is_ready():
            logger.warning("Chat model is not ready; returning availability notice.")
            return "The chat assistant is still loading. Please try again once the models are online."

        prompt = self._build_prompt(history)
        try:
            response = self.llm_service.generate_analysis(prompt)
            return sanitize_human_text(response)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Chat generation failed: %s", exc, exc_info=True)
            return "I encountered an unexpected error while generating a response."

    def _build_prompt(self, history: List[Dict[str, str]]) -> str:
        lines = [self.system_prompt, "", "Conversation log:"]
        for message in history:
            role = sanitize_human_text((message.get("role") or "user").strip()) or "user"
            content = sanitize_human_text((message.get("content") or "").strip())
            if not content:
                continue
            if role.lower() not in {"user", "assistant", "system"}:
                role = "user"
            lines.append(f"[{role.lower()}] {content}")
        lines.append("[assistant]")
        return "\n".join(lines)
