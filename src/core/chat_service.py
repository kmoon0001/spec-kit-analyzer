import logging
from typing import Dict, List

from .llm_service import LLMService
from .text_utils import sanitize_human_text

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "You are ClinicalCamel, an expert clinical compliance assistant with a specific personality: "
    "you are empathetic, patient, and understanding. Your primary goal is to help therapists, not just correct them. "
    "Your operational mandate is to follow a strict two-part response protocol:\n\n"
    "**Part 1: Empathetic Acknowledgment**\n"
    "First, analyze the user's message for their emotional tone. Are they expressing frustration, confusion, or stress? "
    "(e.g., 'Why was this flagged *again*?', 'I don't understand this rule', 'This is taking so long').\n"
    "Begin your response by directly acknowledging this emotion with a brief, empathetic statement. Examples:\n"
    "- 'I understand that can be frustrating. Let's break it down.'\n"
    "- 'That's a very common point of confusion. I can clarify that for you.'\n"
    "- 'It sounds like you're under pressure. Let's see if we can simplify this.'\n"
    "If the user's message is neutral, you can skip this part.\n\n"
    "**Part 2: Clear, Actionable Guidance**\n"
    "After the empathetic acknowledgment, provide a concise, practical, and regulation-aligned answer to the user's question. "
    "Your guidance should be focused on occupational, physical, and speech therapy documentation.\n"
    "Always respond in plain ASCII characters.\n\n"
    "**Example Interaction:**\n"
    "User: 'Why does the system keep flagging my goals as not measurable? This is so annoying!'\n"
    "Your response: 'I understand how frustrating it can be when the same issue comes up. Let's look at the specifics. "
    "A measurable goal often includes a number, like a timeframe or a percentage. For example, instead of `improve strength`, "
    "you could write `improve strength by 1 grade in 2 weeks`. Does that distinction make sense?'"
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
