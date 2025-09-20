from __future__ import annotations
import logging
from typing import Dict, List, Optional
from transformers import pipeline

logger = logging.getLogger(__name__)

class QueryRouterService:
    """
    A service to classify user queries into different intents using a zero-shot
    classification model.
    """
    def __init__(self, model_name: str = "facebook/bart-large-mnli"):
        self.classifier = None
        try:
            logger.info(f"Loading zero-shot classification model: {model_name}")
            self.classifier = pipeline("zero-shot-classification", model=model_name)
            logger.info("Zero-shot classification model loaded successfully.")
        except Exception as e:
            logger.exception(f"Failed to initialize QueryRouterService: {e}")

    def is_ready(self) -> bool:
        return self.classifier is not None

    def classify_query(self, query: str) -> str:
        """
        Classifies the user's query into one of the predefined intents.
        """
        if not self.is_ready():
            logger.warning("Query router is not ready. Defaulting to 'question'.")
            return "question"

        candidate_labels = ["greeting", "question about the document"]
        result = self.classifier(query, candidate_labels)

        top_label = result["labels"][0]
        top_score = result["scores"][0]

        logger.info(f"Query classification result: {result}")

        # If the top score is not very high, we can consider it ambiguous.
        if top_score < 0.7:
            return "ambiguous"

        if top_label == "greeting":
            return "greeting"
        else:
            return "question"
