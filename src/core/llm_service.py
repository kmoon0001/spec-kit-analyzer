import logging
from ctransformers import AutoModelForCausalLM

logger = logging.getLogger(__name__)

class LLMService:
    """
    A service class for interacting with a local Large Language Model.
    """
    def __init__(self, model_repo_id: str, model_filename: str):
        """
        Initializes the LLMService by loading the specified model.
        """
        logger.info(f"Loading model: {model_repo_id}/{model_filename}...")
        try:
            self.llm = AutoModelForCausalLM.from_pretrained(
                model_repo_id,
                model_file=model_filename,
                model_type="mistral",
                gpu_layers=0,  # Change to a non-zero value if you have a GPU
                context_length=4096
            )
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.llm = None

    def is_ready(self) -> bool:
        """
        Checks if the model was loaded successfully.
        """
        return self.llm is not None

    def generate_analysis(self, prompt: str) -> str:
        """
        Generates analysis by running the prompt through the LLM.
        """
        if not self.is_ready():
            logger.error("LLM is not available. Cannot generate analysis.")
            return '{"error": "LLM not available"}'

        logger.info("Generating analysis with the LLM...")
        try:
            raw_text = self.llm(prompt, max_new_tokens=2048, temperature=0.2, top_p=0.95, repetition_penalty=1.1)
            logger.info("LLM analysis generated successfully.")
            return raw_text
        except Exception as e:
            logger.error(f"Error during LLM generation: {e}")
            return f'{{"error": "Failed to generate analysis: {e}"}}'