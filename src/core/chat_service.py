import logging
from typing import List, Dict

from .llm_service import LLMService

logger = logging.getLogger(__name__)


class ChatService:
    """Manages a conversational session with the AI, maintaining history and context."""

    def __init__(self, llm_service: LLMService, initial_context: str):
        """
        Initializes the ChatService with a starting context.

        Args:
            llm_service: The LLM service to use for generating responses.
            initial_context: The initial system prompt or context for the conversation.
        """
        self.llm_service = llm_service
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": initial_context}
        ]

    def get_response(self, user_message: str) -> str:
        """
        Gets a response from the LLM based on the user's message and the conversation history.
        """
        if not self.llm_service.is_ready():
            return "I am currently unable to respond. The AI model is not available."

        try:
            self.history.append({"role": "user", "content": user_message})

            prompt = self._build_prompt_from_history()
            ai_response = self.llm_service.generate_analysis(prompt)

            self.history.append({"role": "assistant", "content": ai_response})

            return ai_response

        except Exception as e:
            logger.error(f"Error getting chat response: {e}", exc_info=True)
            return f"I encountered an error and cannot continue this conversation: {e}"

    def _build_prompt_from_history(self) -> str:
        """Constructs a single prompt string from the conversation history."""
        prompt = ""
        for message in self.history:
            prompt += f"**{message['role'].capitalize()}**: {message['content']}\n\n"
        prompt += "**Assistant**: "
        return prompt
