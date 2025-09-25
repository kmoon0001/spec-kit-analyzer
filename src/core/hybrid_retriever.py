import logging
import numpy as np
from rank_bm25 import BM25Okapi  # type: ignore
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from typing import List, Dict

# Import the database components needed to fetch rules
from ..database import SessionLocal
from .. import crud

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HybridRetriever:
    """
    A retriever that uses a hybrid of keyword-based (BM25) and semantic (dense)
    search to find relevant compliance rules from the application DATABASE.
    """
    def __init__(self, dense_model_name='pritamdeka/S-PubMedBert-MS-MARCO'):
        logging.info("Initializing Hybrid Retriever...")

        # 1. Load rules directly from the database
        self.rules = self._load_rules_from_db()
        if not self.rules:
            logging.warning("No rules loaded from the database. Retriever will be empty.")
            self.corpus = []
            self.bm25 = None
            self.dense_retriever = None
            self.corpus_embeddings = None
            return

        # 2. Build the corpus from the rules
        self.corpus = [
            f"{rule['name']}. {rule['content']}"
            for rule in self.rules
        ]
        logging.info(f"Created a corpus with {len(self.corpus)} rules from the database.")

        # 3. Initialize BM25 with the new corpus
        tokenized_corpus = [doc.lower().split() for doc in self.corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)

        # 4. Initialize the dense retriever and pre-compute embeddings
        logging.info(f"Loading dense retriever model: {dense_model_name}...")
        self.dense_retriever = SentenceTransformer(dense_model_name)
        self.corpus_embeddings = self.dense_retriever.encode(self.corpus, convert_to_tensor=True)
        logging.info("Hybrid Retriever initialized successfully.")

    @staticmethod
    def _load_rules_from_db() -> List[Dict]:
        """Fetches all rubrics from the database on startup."""
        db = None
        try:
            db = SessionLocal()
            # Use the crud function to get all rubrics
            rubric_models = crud.get_rubrics(db, limit=1000) # Get up to 1000 rubrics
            # Convert the SQLAlchemy models to simple dictionaries
            return [{"id": r.id, "name": r.name, "content": r.content} for r in rubric_models]
        except Exception as e:
            logging.error(f"Failed to load rules from database: {e}", exc_info=True)
            return []
        finally:
            if db:
                db.close()

    def retrieve(self, query: str, top_k: int = 5, **kwargs) -> List[Dict]:
        """
        Performs a hybrid search and returns the top_k relevant rules.
        """
        if not self.rules:
            return []

        # --- BM25 Search (Keyword-based) ---
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)

        # --- Dense Retriever Search (Semantic) ---
        query_embedding = self.dense_retriever.encode(query, convert_to_tensor=True)
        cosine_scores = cos_sim(query_embedding, self.corpus_embeddings)[0].cpu().numpy()

        # --- Reciprocal Rank Fusion (RRF) for combining results ---
        k = 60
        bm25_ranks = {i: rank + 1 for rank, i in enumerate(np.argsort(bm25_scores)[::-1])}
        dense_ranks = {i: rank + 1 for rank, i in enumerate(np.argsort(cosine_scores)[::-1])}

        rrf_scores = {}
        all_indices = set(bm25_ranks.keys()) | set(dense_ranks.keys())

        for idx in all_indices:
            rrf_score = 0.0
            if idx in bm25_ranks:
                rrf_score += 1.0 / (k + bm25_ranks[idx])
            if idx in dense_ranks:
                rrf_score += 1.0 / (k + dense_ranks[idx])
            rrf_scores[idx] = rrf_score

        # Sort by RRF score and return the top_k rule dictionaries
        sorted_fused_indices = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        top_k_results = [self.rules[i] for i in sorted_fused_indices[:top_k]]
        return top_k_results
