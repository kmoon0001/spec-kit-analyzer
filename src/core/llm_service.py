"""LLM Service for managing local language models using transformers."""

from threading import Lock
from typing import Any, Dict, Optional

import structlog
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = structlog.get_logger(__name__)


class LLMService:
    """
    A thread-safe, lazy-loading service for managing a local language model.

    This service ensures that the large language model is only loaded into memory
    when it is first needed, reducing the application's initial memory footprint.
    It is designed to be thread-safe to prevent race conditions during model loading
    in concurrent environments.
    """

    _instance = None
    _lock = Lock()

    def __init__(
        self,
        model_repo_id: str,
        model_filename: str,
        llm_settings: Optional[Dict[str, Any]] = None,
        revision: Optional[str] = None,
    ):
        """
        Initializes the LLM Service configuration without loading the model.

        Args:
            model_repo_id (str): The Hugging Face repository ID for the model.
            model_filename (str): Ignored for transformers (kept for compatibility).
            llm_settings (dict, optional): A dictionary of settings for the model.
            revision (str, optional): The specific model revision (commit hash) to use.
        """
        self.model_repo_id = model_repo_id
        self.model_filename = model_filename  # Not used but kept for compatibility
        self.settings = llm_settings or {}
        self.revision = revision
        self.llm = None  # The model will be loaded lazily.
        self.tokenizer = None
        self.is_loading = False

    def _load_model(self):
        """
        Loads the model using transformers library.
        This method is intended to be called internally and is not thread-safe by itself.
        """
        if self.llm:
            return

        self.is_loading = True
        try:
            logger.info(
                "Loading LLM with transformers",
                model_repo_id=self.model_repo_id,
            )

            # Use FLAN-T5-small - excellent for instruction-following and Q&A
            # 308MB, optimized for tasks like compliance analysis
            model_id = "google/flan-t5-small"  # 308MB, great for instructions

            # Import T5 models
            from transformers import T5ForConditionalGeneration, T5Tokenizer

            # Load tokenizer and model
            self.tokenizer = T5Tokenizer.from_pretrained(model_id)

            self.llm = T5ForConditionalGeneration.from_pretrained(
                model_id,
                torch_dtype=torch.float32,  # Use float32 for CPU
                device_map="cpu",
                low_cpu_mem_usage=True,
            )

            # T5 doesn't need pad token setup like GPT models

            logger.info("LLM loaded successfully with transformers")
        except Exception as e:
            logger.critical(
                "Fatal error: Failed to load LLM", error=str(e), exc_info=True
            )
            self.llm = None
            self.tokenizer = None
        finally:
            self.is_loading = False

    def _ensure_model_loaded(self):
        """
        Ensures the model is loaded before use. This method is thread-safe.
        """
        if self.llm or self.is_loading:
            return
        with self._lock:
            # Double-check locking to prevent multiple threads from loading the model.
            if not self.llm:
                self._load_model()

    def is_ready(self) -> bool:
        """
        Checks if the LLM is loaded and ready for inference.
        This will trigger the model to load if it hasn't been already.
        """
        self._ensure_model_loaded()
        return self.llm is not None and self.tokenizer is not None

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generates text using the loaded LLM.

        If the model is not loaded, it will be loaded on the first call.

        Args:
            prompt (str): The input text prompt for the model.
            **kwargs: Additional generation parameters to override defaults.

        Returns:
            A string containing the generated text or an error message.
        """
        if not self.is_ready():
            logger.error(
                "LLM is not available or failed to load. Cannot generate text."
            )
            return "Error: LLM service is not available."

        try:
            # Combine default and call-specific generation parameters.
            gen_params = self.settings.get("generation_params", {}).copy()
            gen_params.update(kwargs)

            # Get parameters
            max_new_tokens = gen_params.pop("max_new_tokens", 512)
            temperature = gen_params.pop("temperature", 0.1)

            logger.debug(
                "Generating text with transformers",
                max_new_tokens=max_new_tokens,
                temperature=temperature,
            )

            if self.llm is None or self.tokenizer is None:
                logger.error("LLM model or tokenizer is not loaded")
                return "Error: LLM model is not available."

            # Tokenize input (T5 uses encoder-decoder architecture)
            inputs = self.tokenizer(
                prompt, return_tensors="pt", truncation=True, max_length=512
            )

            # Generate with T5
            with torch.no_grad():
                outputs = self.llm.generate(
                    **inputs,
                    max_length=max_new_tokens,  # T5 uses max_length not max_new_tokens
                    temperature=temperature if temperature > 0 else 1.0,
                    do_sample=temperature > 0,
                    top_p=0.9,
                    num_beams=2,  # Use beam search for better quality
                )

            # Decode the output (T5 generates full sequence)
            generated_text = self.tokenizer.decode(
                outputs[0], skip_special_tokens=True
            ).strip()

            return generated_text

        except Exception as e:
            logger.error(
                "An error occurred during text generation", error=str(e), exc_info=True
            )
            return "An error occurred during text generation."

    def generate_analysis(self, prompt: str, **kwargs) -> str:
        """
        Alias for generate method to maintain compatibility with other services.

        Args:
            prompt (str): The input text prompt for analysis.
            **kwargs: Additional generation parameters.

        Returns:
            A string containing the generated analysis.
        """
        return self.generate(prompt, **kwargs)
