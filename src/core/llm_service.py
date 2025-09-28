import json
import logging
from typing import Any, Dict

from ctransformers import AutoModelForCausalLM  # type: ignore

logger = logging.getLogger(__name__)


class LLMService:
    """Service wrapper around a local GGUF model loaded via ctransformers."""

    def __init__(
        self, model_repo_id: str, model_filename: str, llm_settings: Dict[str, Any]
    ) -> None:
        self.llm = None
        self.generation_params = llm_settings.get("generation_params", {})
        logger.info("Loading GGUF model: %s/%s", model_repo_id, model_filename)
        try:
            self.llm = AutoModelForCausalLM.from_pretrained(
                model_repo_id,
                model_file=model_filename,
                model_type=llm_settings.get("model_type", "llama"),
                gpu_layers=llm_settings.get("gpu_layers", 0),
                context_length=llm_settings.get("context_length", 2048),
            )
            logger.info("GGUF model loaded successfully.")
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to load GGUF model: %s", exc, exc_info=True)
            raise RuntimeError(f"Could not load LLM model: {exc}") from exc

    def is_ready(self) -> bool:
        return self.llm is not None

    def generate_analysis(self, prompt: str) -> str:
        if not self.is_ready():
            logger.error("LLM is not available. Cannot generate analysis.")
            return '{"error": "LLM not available"}'

        assert self.llm is not None  # for type-checkers
        logger.info("Generating response with the LLM...")
        try:
            return self.llm(prompt, **self.generation_params)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Error during LLM generation: %s", exc, exc_info=True)
            return '{"error": "Generation failed"}'

    def parse_json_output(self, result: str) -> Dict[str, Any]:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            logger.error("LLM returned invalid JSON payload: %s", result)
            return {"raw_output": result}

    def generate_personalized_tip(self, finding: Dict[str, Any]) -> str:
        if not self.is_ready():
            return finding.get("suggestion", "No tip available.")

        issue_title = finding.get("issue_title", "Compliance issue")
        issue_detail = finding.get("issue_detail", "")
        context = finding.get("text", "")

        prompt = (
            "You are a compliance coach. Provide a concise, actionable tip for the "
            "following issue.\n"
            f"Issue: {issue_title}\n"
            f"Detail: {issue_detail}\n"
            f"Excerpt: {context}\n"
            "Tip:"
        )

        response = self.generate_analysis(prompt)
        return response.strip()
