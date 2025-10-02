"""LLM Service for managing local language models using llama-cpp-python."""

from threading import Lock
from typing import Any, Dict, Optional

import structlog

# Import llama-cpp-python for GGUF model support
from llama_cpp import Llama

logger = structlog.get_logger(__name__)


class LLMService:
    """
    A thread-safe, lazy-loading service for managing a local GGUF model.

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
            model_filename (str): The specific GGUF model file to use.
            llm_settings (dict, optional): A dictionary of settings for ctransformers.
            revision (str, optional): The specific model revision (commit hash) to use.
        """
        self.model_repo_id = model_repo_id
        self.model_filename = model_filename
        self.settings = llm_settings or {}
        self.revision = revision
        self.llm = None  # The model will be loaded lazily.
        self.is_loading = False

    def _load_model(self):
        """
        Loads the GGUF model using llama-cpp-python.
        This method is intended to be called internally and is not thread-safe by itself.
        """
        if self.llm:
            return

        self.is_loading = True
        try:
            logger.info(
                "Loading LLM with llama-cpp-python",
                model_repo_id=self.model_repo_id,
                model_filename=self.model_filename,
            )

            # Download model from Hugging Face if needed
            from huggingface_hub import hf_hub_download

            model_path = hf_hub_download(
                repo_id=self.model_repo_id,
                filename=self.model_filename,
                revision=self.revision,
            )

            # Get settings
            context_length = self.settings.get("context_length", 2048)
            n_threads = self.settings.get("n_threads", 4)

            # Load model with llama-cpp-python
            self.llm = Llama(
                model_path=model_path,
                n_ctx=context_length,
                n_threads=n_threads,
                verbose=False,
            )
            logger.info("LLM loaded successfully with llama-cpp-python")
        except Exception as e:
            logger.critical(
                "Fatal error: Failed to load LLM", error=str(e), exc_info=True
            )
            self.llm = None
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
        return self.llm is not None

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

            # Map parameter names for llama-cpp-python
            max_tokens = gen_params.pop("max_new_tokens", 512)
            temperature = gen_params.pop("temperature", 0.1)

            logger.debug(
                "Generating text with llama-cpp-python",
                max_tokens=max_tokens,
                temperature=temperature,
            )

            if self.llm is None:
                logger.error("LLM model is not loaded")
                return "Error: LLM model is not available."

            # Generate with llama-cpp-python
            response = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["</s>", "\n\n"],
                echo=False,
            )

            # Extract text from response
            generated_text = response["choices"][0]["text"].strip()
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
