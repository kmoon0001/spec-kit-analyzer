import os
import torch
from sentence_transformers import SentenceTransformer, util
from typing import List, Dict

from src.utils import chunk_text

class KnowledgeBaseService:
    """
    Manages the creation and querying of a knowledge base using sentence embeddings.
    """
    def __init__(self, model_name: str = 'pritamdeka/S-PubMedBert-MS-MARCO', device: str = None):
        """
        Initializes the service, loading the sentence transformer model.
        """
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"KnowledgeBase: Using device '{device}' for sentence transformer.")
        self.model = SentenceTransformer(model_name, device=device)
        self.corpus_chunks: List[str] = []
        self.corpus_embeddings: torch.Tensor = None
        self._is_ready = False

    def is_ready(self) -> bool:
        """Returns True if the knowledge base has been built."""
        return self._is_ready

    def build_from_text(self, text: str):
        """
        Builds the knowledge base from a single string of text.
        """
        print("KnowledgeBase: Building from provided text...")

        if not text or not isinstance(text, str):
            print("KnowledgeBase: Error - No text provided to build knowledge base.")
            return

        # 1. Split the text into manageable chunks
        # Using a smaller chunk size for more granular context for the RAG model.
        self.corpus_chunks = chunk_text(text, max_chars=750)
        print(f"KnowledgeBase: Split text into {len(self.corpus_chunks)} chunks.")

        if not self.corpus_chunks:
            print("KnowledgeBase: Error - Text splitting resulted in no chunks.")
            return

        # 2. Encode the chunks into embeddings
        print("KnowledgeBase: Encoding chunks into embeddings... (This may take a moment)")
        with torch.no_grad():
            self.corpus_embeddings = self.model.encode(
                self.corpus_chunks,
                convert_to_tensor=True,
                show_progress_bar=True
            )

        self._is_ready = True
        print("KnowledgeBase: Build complete.")

    def find_relevant_chunks(self, question: str, top_k: int = 5) -> List[Dict[str, any]]:
        """
        Finds the most relevant text chunks for a given question.
        Returns a list of dictionaries, each containing the chunk and its score.
        """
        if not self.is_ready() or self.corpus_embeddings is None:
            return [{"text": "Error: Knowledge base is not ready.", "score": 0.0}]

        # 1. Encode the question
        question_embedding = self.model.encode(question, convert_to_tensor=True)

        # 2. Compute cosine similarity between the question and all chunks
        cos_scores = util.cos_sim(question_embedding, self.corpus_embeddings)[0]

        # 3. Find the top_k best scores
        top_results = torch.topk(cos_scores, k=min(top_k, len(self.corpus_chunks)))

        # 4. Format and return the results
        results = []
        for score, idx in zip(top_results[0], top_results[1]):
            results.append({
                "text": self.corpus_chunks[idx],
                "score": score.item()
            })

        return results
