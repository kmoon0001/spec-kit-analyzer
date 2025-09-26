import logging
import pickle
from ctransformers import AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
import torch

from src.config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    """
    A service class to handle interactions with the local Large Language Model (LLM)
    and the sentence embedding model.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        Initializes the LLM and embedding models based on the application config.
        This is a Singleton pattern to ensure models are loaded only once.
        """
        if self._initialized:
            return

        logger.info("Initializing LLMService...")

        # Load LLM for text generation
        self.llm = AutoModelForCausalLM.from_pretrained(
            config.llm.model_path,
            model_type=config.llm.model_type,
            lib=config.llm.lib,
            gpu_layers=config.llm.gpu_layers,
            temperature=config.llm.temperature,
            top_p=config.llm.top_p,
            top_k=config.llm.top_k,
            repetition_penalty=config.llm.repetition_penalty
        )

        # Load model for generating semantic embeddings
        self.embedding_model = SentenceTransformer(config.embedding.model_name)

        logger.info("LLMService initialized successfully.")
        self._initialized = True

    def make_request(self, prompt: str) -> str:
        """
        Sends a prompt to the LLM and returns the generated text.
        """
        logger.info("Sending prompt to LLM...")
        response = self.llm(prompt, max_new_tokens=config.llm.max_new_tokens, stream=False)
        logger.info("Received response from LLM.")
        return response

    def get_embedding(self, text: str) -> bytes:
        """
        Generates a semantic embedding for the given text.
        """
        logger.info("Generating embedding...")
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        logger.info("Embedding generated.")
        # Serialize the numpy array for storage
        return pickle.dumps(embedding)