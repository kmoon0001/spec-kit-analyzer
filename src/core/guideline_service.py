from src.core.hybrid_retriever import HybridRetriever
from typing import List

class GuidelineService:
    """
    A service to retrieve relevant compliance guidelines using a hybrid search approach.
    """
    def __init__(self):
        # Initialize the retriever. The retriever will build its own index on init.
        self.retriever = HybridRetriever()

    def get_relevant_guidelines(self, text: str) -> List[str]:
        """
        Retrieves guidelines relevant to the input text.

        Args:
            text: The text to find relevant guidelines for.

        Returns:
            A list of relevant guideline strings.
        """
        # The retriever's search method returns a list of document contents
        return self.retriever.search(text)