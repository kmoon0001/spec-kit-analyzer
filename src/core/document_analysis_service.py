import logging
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from src.utils import load_config

logger = logging.getLogger(__name__)

class DocumentAnalysisService:
    """
    Manages the analysis of a single document by creating an in-memory FAISS index
    of its chunks and allowing for semantic search.
    """

    def __init__(self, chunks: list[dict]):
        """
        Initializes the DocumentAnalysisService.

        Args:
            chunks (list[dict]): A list of chunks from the smart_chunker.
                                 Each chunk is a dict with 'sentence', 'window', and 'metadata'.
        """
        self.config = load_config()
        model_name = self.config['models']['retriever']

        self.chunks = chunks
        self.is_index_ready = False
        self.faiss_index = None

        logger.info(f"Loading Sentence Transformer model: {model_name}")
        self.model = SentenceTransformer(model_name)

        self._build_index()
        logger.info("DocumentAnalysisService initialized.")

    def _build_index(self):
        """Builds an in-memory FAISS index from the document chunks."""
        if not self.chunks:
            logger.warning("No chunks provided to build the index.")
            return

        logger.info("Encoding document chunks into vectors...")
        # We search based on the core sentence, not the whole window
        texts_to_encode = [chunk['sentence'] for chunk in self.chunks]

        embeddings = self.model.encode(texts_to_encode, convert_to_tensor=False, show_progress_bar=False)

        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)

        embedding_dim = embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatL2(embedding_dim)
        self.faiss_index.add(embeddings)

        self.is_index_ready = True
        logger.info(f"Successfully indexed {len(self.chunks)} document chunks.")

    def search(self, query: str, top_k: int = 5, metadata_filter: dict = None) -> list[dict]:
        """
        Performs a FAISS similarity search through the document chunks.

        Args:
            query (str): The search query.
            top_k (int): The number of top results to return.
            metadata_filter (dict): A dictionary to filter chunks by metadata before searching.

        Returns:
            list[dict]: A list of the top matching chunks.
        """
        if not self.is_index_ready or not self.faiss_index:
            logger.warning("Search called before the index was ready.")
            return []

        # 1. Pre-filtering (if a filter is provided)
        candidate_chunks = self.chunks
        if metadata_filter:
            candidate_chunks = [
                chunk for chunk in self.chunks
                if all(item in chunk['metadata'].items() for item in metadata_filter.items())
            ]
            if not candidate_chunks:
                return [] # No chunks matched the filter

        # 2. Embedding and Searching
        # For now, we search on all chunks and filter later. A more advanced implementation
        # would re-build a temporary index from the filtered chunks.
        query_embedding = self.model.encode([query])
        if query_embedding.dtype != np.float32:
            query_embedding = query_embedding.astype(np.float32)

        # We need to search for more results initially, as some might be filtered out
        search_k = top_k * 3 if metadata_filter else top_k
        distances, indices = self.faiss_index.search(query_embedding, search_k)

        # 3. Post-filtering and result assembly
        results = []
        # Get the indices of the candidate chunks for quick lookup
        candidate_indices = {i for i, chunk in enumerate(self.chunks) if chunk in candidate_chunks}

        for i in indices[0]:
            if i != -1 and i in candidate_indices:
                results.append(self.chunks[i])
            if len(results) == top_k:
                break

        return results
