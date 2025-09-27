import asyncio
import logging
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from ..database import crud
from ..config import get_settings, Settings

# Enhanced logging setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    A sophisticated retriever that combines keyword-based (BM25) and semantic
    (dense) search to find relevant compliance rules from the database.

    This version is designed for production with asynchronous loading, caching,
    and proper dependency injection.
    """

    _instance = None
    _is_initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(HybridRetriever, cls).__new__(cls)
        return cls._instance

    def __init__(
        self, settings: Optional[Settings] = None, db: Optional[Session] = None
    ):
        if self._is_initialized and self.settings == settings:
            return

        self.settings = settings or get_settings()
        self.db = db
        self.rules: List[Dict[str, Any]] = []
        self.corpus: List[str] = []
        self.bm25: Optional[BM25Okapi] = None
        self.dense_retriever: Optional[SentenceTransformer] = None
        self.corpus_embeddings: Optional[np.ndarray] = None
        self._is_initialized = False

        logger.info(
            "HybridRetriever instance created. Call `initialize` to load models and data."
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying model/data loading... Attempt #{retry_state.attempt_number}"
        ),
    )
    async def initialize(self):
        """
        Asynchronously initializes the retriever, loading models and data.
        This method is designed to be called once during application startup.
        """
        if self._is_initialized:
            logger.info("HybridRetriever is already initialized.")
            return

        logger.info("Initializing HybridRetriever...")

        # 1. Load rules from the database
        await self._load_rules_from_db_async()
        if not self.rules:
            logger.warning(
                "No rules loaded from the database. Retriever will be non-functional."
            )
            self._is_initialized = True
            return

        # 2. Build the corpus
        self.corpus = [f"{rule['name']}. {rule['content']}" for rule in self.rules]
        logger.info(f"Created a corpus with {len(self.corpus)} rules.")

        # 3. Initialize BM25 with the corpus
        tokenized_corpus = [doc.lower().split() for doc in self.corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)

        # 4. Initialize the dense retriever and pre-compute embeddings
        model_name = self.settings.dense_model_name
        logger.info(f"Loading dense retriever model: {model_name}...")
        self.dense_retriever = SentenceTransformer(model_name)

        logger.info("Encoding corpus... This may take a moment.")
        self.corpus_embeddings = self.dense_retriever.encode(
            self.corpus, convert_to_tensor=True, show_progress_bar=True
        )

        self._is_initialized = True
        logger.info("HybridRetriever initialized successfully.")

    async def _load_rules_from_db_async(self):
        """
        Asynchronously fetches all rubrics from the database using an async session.
        """
        if self.db:  # If a db session was provided at initialization
            session = self.db
            close_session = False
        else:
            from ..database import AsyncSessionLocal

            session = AsyncSessionLocal()
            close_session = True

        try:
            logger.info("Loading rules from the database asynchronously...")
            rubric_models = await crud.get_rubrics(session, limit=1000)
            self.rules = [
                {
                    "id": r.id,
                    "name": r.name,
                    "content": r.content,
                    "category": r.category,
                }
                for r in rubric_models
            ]
            logger.info(f"Successfully loaded {len(self.rules)} rules.")
        except Exception as e:
            logger.error(f"Failed to load rules from database: {e}", exc_info=True)
            self.rules = []
        finally:
            if close_session:
                await session.close()

    def _perform_sync_retrieval(
        self, query: str, indices_to_search: List[int]
    ) -> List[int]:
        """
        Synchronous part of the retrieval logic. This is run in a thread pool to avoid
        blocking the asyncio event loop.
        """
        # --- BM25 Search (Keyword-based) on the filtered subset ---
        tokenized_query = query.lower().split()
        filtered_corpus = [self.corpus[i] for i in indices_to_search]
        tokenized_filtered_corpus = [doc.lower().split() for doc in filtered_corpus]

        if not tokenized_filtered_corpus:
            return []

        temp_bm25 = BM25Okapi(tokenized_filtered_corpus)
        bm25_scores = temp_bm25.get_scores(tokenized_query)

        # --- Dense Retriever Search (Semantic) on the filtered subset ---
        query_embedding = self.dense_retriever.encode(query, convert_to_tensor=True)

        corpus_embeddings_tensor = self.corpus_embeddings[indices_to_search]

        cosine_scores_tensor = cos_sim(query_embedding, corpus_embeddings_tensor)[0]
        cosine_scores = cosine_scores_tensor.cpu().numpy()

        # --- Reciprocal Rank Fusion (RRF) for combining results ---
        # RRF is a method to combine multiple ranked lists into a single, more robust
        # list. It's resilient to poorly performing retrievers because it focuses on
        # the rank of a document, not its absolute score.
        # The formula is: RRF_Score(d) = sum(1 / (k + rank_i(d))) for each list i.
        # 'k' is a constant that mitigates the influence of high ranks from a single retriever.
        k = self.settings.rrf_k

        # Create a mapping from the temporary index (in the filtered list) back to the original rule index
        idx_map = dict(enumerate(indices_to_search))

        # Get the rank of each document for both BM25 and dense retrieval results.
        # The rank is its position in the sorted list (e.g., the best item has rank 1).
        bm25_ranks = {
            idx_map[i]: rank + 1 for rank, i in enumerate(np.argsort(bm25_scores)[::-1])
        }
        dense_ranks = {
            idx_map[i]: rank + 1
            for rank, i in enumerate(np.argsort(cosine_scores)[::-1])
        }

        rrf_scores = {}
        # Consider all unique documents returned by either retriever
        all_indices = set(bm25_ranks.keys()) | set(dense_ranks.keys())

        # Calculate the RRF score for each document
        for idx in all_indices:
            rrf_score = 0.0
            if idx in bm25_ranks:
                rrf_score += 1.0 / (k + bm25_ranks[idx])
            if idx in dense_ranks:
                rrf_score += 1.0 / (k + dense_ranks[idx])
            rrf_scores[idx] = rrf_score

        # Sort by RRF score and return the sorted indices
        sorted_fused_indices = sorted(
            rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True
        )
        return sorted_fused_indices

    async def retrieve(
        self, query: str, top_k: int = 5, category_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Performs a hybrid search by offloading the CPU-bound work to a thread pool,
        making the operation non-blocking for the asyncio event loop.
        """
        if not self._is_initialized or not self.rules:
            logger.warning(
                "Retriever is not initialized or has no rules. Returning empty list."
            )
            return []

        # Filter rules by category if a filter is provided (this is fast)
        if category_filter:
            indices_to_search = [
                i
                for i, rule in enumerate(self.rules)
                if rule.get("category") == category_filter
            ]
            if not indices_to_search:
                logger.info(f"No rules found for category: {category_filter}")
                return []
        else:
            indices_to_search = list(range(len(self.rules)))

        # Offload the blocking, CPU-bound search logic to a separate thread
        sorted_fused_indices = await asyncio.to_thread(
            self._perform_sync_retrieval, query, indices_to_search
        )

        # Return the top_k rule dictionaries based on the sorted indices
        top_k_results = [self.rules[i] for i in sorted_fused_indices[:top_k]]
        return top_k_results


# No singleton instance here. The instance is managed by the dependency
# injection system in `api/dependencies.py` to improve testability and
# separation of concerns.
