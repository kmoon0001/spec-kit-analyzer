import logging
from typing import List, Dict, Any

from .llm_service import LLMService

logger = logging.getLogger(__name__)

class ChatService:
    """
    Manages a conversational session with the AI, maintaining history and context.
    """
    def __init__(self, llm_service: LLMService, initial_context: str):
        """
        Initializes the ChatService with a starting context.

        Args:
            llm_service: The LLM service to use for generating responses.
            initial_context: The initial system prompt or context for the conversation (e.g., the details of a compliance finding).
        """
        self.llm_service = llm_service
        # The history will store the conversation in the format the LLM expects
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": initial_context}
        ]

    def get_response(self, user_message: str) -> str:
        """
        Gets a response from the LLM based on the user's message and the conversation history.

        Args:
            user_message: The user's latest message.

        Returns:
            The AI's response as a string.
        """
        if not self.llm_service.is_ready():
            return "I am currently unable to respond. The AI model is not available."

        try:
            # Add the user's message to the history
            self.history.append({"role": "user", "content": user_message})

            # The llm_service.generate_analysis method might need to be adapted
            # to handle a list of messages (the history) instead of a single prompt string.
            # For now, we will construct a single string, but a future enhancement would be
            # to update the LLM service to handle conversational history directly.
            
            prompt = self._build_prompt_from_history()
            ai_response = self.llm_service.generate_analysis(prompt)

            # Add the AI's response to the history
            self.history.append({"role": "assistant", "content": ai_response})

            return ai_response

        except Exception as e:
            logger.error(f"Error getting chat response: {e}", exc_info=True)
            return f"I encountered an error and cannot continue this conversation: {e}"

    def _build_prompt_from_history(self) -> str:
        """
        Constructs a single prompt string from the conversation history.
        This is a simplified approach. A more advanced LLM service might handle the history directly.
        """
        prompt = ""
        for message in self.history:
            prompt += f"**{message['role'].capitalize()}**: {message['content']}\n\n"
        prompt += "**Assistant**: "
        return prompt
