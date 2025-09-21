from __future__ import annotations

import json
import logging
from typing import List, Dict

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class ContextService:
    """
    A service for classifying the context of sentences using sentence embeddings.
    """

    def __init__(self, categories_path: str, model: SentenceTransformer):
        """
        Initializes the service by loading category definitions and pre-computing
        embeddings.

        Args:
            categories_path (str): Path to the JSON file with category
                                 definitions.
            model (SentenceTransformer): An already loaded SentenceTransformer
                                         model instance.
        """
        self.model = model
        self.categories: Dict[str, str] = {}
        self.category_names: List[str] = []
        self.category_embeddings: Optional[np.ndarray] = None

        try:
            logger.info(f"Loading context categories from {categories_path}")
            with open(categories_path, 'r', encoding='utf-8') as f:
                self.categories = json.load(f)

            self.category_names = list(self.categories.keys())
            category_descriptions = list(self.categories.values())

            logger.info("Pre-computing embeddings for context categories...")
            self.category_embeddings = self.model.encode(category_descriptions)
            logger.info("Context category embeddings computed successfully.")

        except FileNotFoundError:
            logger.exception(
                f"Context categories file not found at {categories_path}. "
                f"The service will be disabled."
            )
        except Exception:
            logger.exception("Failed to initialize ContextService")

    def is_ready(self) -> bool:
        """Check if the service is ready to classify sentences."""
        return self.category_embeddings is not None

    def classify_sentence(self, sentence: str) -> Optional[str]:
        """
        Classifies a single sentence into one of the predefined categories.

        Args:
            sentence (str): The sentence to classify.

        Returns:
            Optional[str]: The name of the best-matching category, or None if
                         classification fails.
        """
        if not self.is_ready() or self.category_embeddings is None:
            return None

        try:
            # 1. Compute the embedding for the input sentence
            sentence_embedding = self.model.encode([sentence])

            # 2. Calculate cosine similarity
            similarities = cosine_similarity(
                sentence_embedding, self.category_embeddings
            )

            # 3. Find the index of the category with the highest similarity
            best_match_index = np.argmax(similarities)

            return self.category_names[best_match_index]
        except Exception:
            logger.exception(f"Failed to classify sentence: '{sentence[:50]}...'")
            return None
