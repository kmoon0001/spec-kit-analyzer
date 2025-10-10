import logging

from .text_utils import sanitize_human_text

logger = logging.getLogger(__name__)

# --- Mixture of Experts Definitions ---

DEFAULT_EXPERT = (
    "You are ClinicalCamel, a concise clinical compliance assistant."
    " Respond in English using plain ASCII characters."
    " Provide practical, regulation-aligned guidance for occupational, physical,"
    " and speech therapy documentation."
)

MEDICARE_EXPERT = "You are a Medicare documentation expert. Your role is to provide precise, authoritative guidance on Medicare regulations, including Part A and Part B. Focus on rules for skilled services, maintenance therapy, and proper G-code usage. Cite specific regulations when possible."

BILLING_EXPERT = "You are a clinical billing and coding expert. You specialize in CPT codes for therapy services. Your answers should be focused on avoiding common billing errors, ensuring documentation supports the codes used, and explaining the appropriate use of timed vs. untimed codes."

SOAP_NOTE_EXPERT = "You are an expert in structuring clinical notes. You specialize in the SOAP (Subjective, Objective, Assessment, Plan) format. Your guidance should focus on what information belongs in each section and how to write a defensible assessment that justifies the plan of care."


class MixtureOfExpertsRouter:
    """Routes a query to the best expert based on keywords."""

    def __init__(self):
        self.experts = {
            "medicare": {
                "prompt": MEDICARE_EXPERT,
                "keywords": ["medicare", "g-code", "part a", "part b", "8-minute rule"],
            },
            "billing": {
                "prompt": BILLING_EXPERT,
                "keywords": ["cpt", "code", "billing", "charge", "timed", "un-timed"],
            },
            "soap": {"prompt": SOAP_NOTE_EXPERT, "keywords": ["soap", "subjective", "objective", "assessment", "plan"]},
        }

    def route(self, query: str) -> str:
        """Selects the best expert prompt based on the query."""
        query_lower = query.lower()
        for expert_name, config in self.experts.items():
            if any(keyword in query_lower for keyword in config["keywords"]):
                logger.info("Routing query to %s expert.", expert_name)
                return config["prompt"]

        logger.info("Routing query to default expert.")
        return DEFAULT_EXPERT


# --- Refactored Chat Service --- #
# --- Refactored Chat Service --- #
# --- Refactored Chat Service --- #


class ChatService:
    """Conversational service using a Mixture of Experts."""

    def process_message(self, history: list[dict[str, str]]) -> str:
        if not self.llm_service.is_ready():
            logger.warning("Chat model is not ready; returning availability notice.")
            return "The chat assistant is still loading. Please try again once the models are online."

        # Get the latest user query to determine the expert
        latest_query = ""
        if history and history[-1]["role"].lower() == "user":
            latest_query = history[-1]["content"]

        # Route to the best expert and get the system prompt
        system_prompt = self.router.route(latest_query)

        prompt = self._build_prompt(history, system_prompt)
        try:
            response = self.llm_service.generate_analysis(prompt)
            return sanitize_human_text(response)
        except Exception as exc:
            logger.error("Chat generation failed: %s", exc, exc_info=True)
            return "I encountered an unexpected error while generating a response."

    def _build_prompt(self, history: list[dict[str, str]], system_prompt: str) -> str:
        lines = [system_prompt, "", "Conversation log:"]
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
