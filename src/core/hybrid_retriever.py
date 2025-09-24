import logging
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from typing import List

from src.rubric_service import RubricService, ComplianceRule

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HybridRetriever:
    """
    A retriever that uses a hybrid of keyword-based (BM25) and semantic (dense)
    search to find relevant compliance rules from the knowledge graph.
    """
    def __init__(self, dense_model_name='pritamdeka/S-PubMedBert-MS-MARCO'):
        logging.info("Initializing Hybrid Retriever with GraphRAG capabilities...")

        # 1. Load rules from the RubricService
        self.rubric_service = RubricService()
        self.rules: List[ComplianceRule] = self.rubric_service.get_rules()
        if not self.rules:
            logging.warning("No rules loaded from RubricService. Retriever will be empty.")
            self.corpus = []
            self.bm25 = None
            self.dense_retriever = None
            self.corpus_embeddings = None
            return

        # 2. Build the corpus from the rules
        # We'll create a text representation of each rule to be used for searching.
        self.corpus = [
            f"{rule.issue_title}. {rule.issue_detail} {rule.suggestion}"
            for rule in self.rules
        ]
        logging.info(f"Created a corpus with {len(self.corpus)} rules.")

        # 3. Initialize BM25 with the new corpus
        tokenized_corpus = [doc.lower().split() for doc in self.corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)
        logging.info("BM25 index created from compliance rules.")

        # 4. Initialize the dense retriever and pre-compute embeddings
        logging.info(f"Loading dense retriever model: {dense_model_name}...")
        self.dense_retriever = SentenceTransformer(dense_model_name)
        logging.info("Pre-computing embeddings for the rule corpus... (This may take a moment)")
        self.corpus_embeddings = self.dense_retriever.encode(self.corpus, convert_to_tensor=True)
        logging.info("Corpus embeddings for rules created successfully.")

        logging.info("Hybrid Retriever (GraphRAG) initialized successfully.")

    def search(self, query: str, top_k: int = 5, discipline: str = "All", doc_type: str = "Unknown") -> List[ComplianceRule]:
        """
        Performs a hybrid search and returns the top_k relevant ComplianceRule objects,
        filtered by discipline and document type.

        Args:
            query (str): The search query (e.g., a snippet from a clinical document).
            top_k (int): The number of results to return.
            discipline (str): The discipline to filter by (e.g., 'pt', 'ot', 'slp').
            doc_type (str): The document type to filter by (e.g., 'Evaluation').

        Returns:
            List[ComplianceRule]: A list of the most relevant compliance rules.
        """
        if not self.rules:
            logging.warning("Retriever is not initialized with rules. Returning empty list.")
            return []

        logging.info(f"\nPerforming hybrid search for query: '{query}'")

        # --- Filter rules first ---
        # This is more efficient than searching all rules and then filtering.
        filtered_indices_map = {
            original_index: rule
            for original_index, rule in enumerate(self.rules)
            if (discipline == "All" or rule.discipline.lower() == discipline.lower()) and \
               (doc_type == "Unknown" or rule.document_type is None or rule.document_type == doc_type)
        }

        if not filtered_indices_map:
            logging.warning(f"No rules found for discipline '{discipline}' and doc_type '{doc_type}'.")
            return []

        filtered_original_indices = list(filtered_indices_map.keys())

        # Create a filtered corpus and embeddings view for searching
        filtered_corpus = [self.corpus[i] for i in filtered_original_indices]
        filtered_corpus_embeddings = self.corpus_embeddings[filtered_original_indices]

        # --- BM25 Search (Keyword-based) on filtered corpus ---
        tokenized_query = query.lower().split()
        # We need a new BM25 index for the filtered corpus
        filtered_tokenized_corpus = [doc.lower().split() for doc in filtered_corpus]
        filtered_bm25 = BM25Okapi(filtered_tokenized_corpus)
        bm25_scores = filtered_bm25.get_scores(tokenized_query)

        # --- Dense Retriever Search (Semantic) on filtered corpus ---
        query_embedding = self.dense_retriever.encode(query, convert_to_tensor=True)
        cosine_scores = cos_sim(query_embedding, filtered_corpus_embeddings)[0]

        # --- Reciprocal Rank Fusion (RRF) for combining results ---
        # RRF is generally better than simple union. It considers the rank of each result.
        # k is a constant, usually 60.
        k = 60

        # Get ranks from both retrievers
        bm25_ranks = {i: rank + 1 for rank, i in enumerate(np.argsort(bm25_scores)[::-1])}
        dense_ranks = {i: rank + 1 for rank, i in enumerate(np.argsort(cosine_scores.cpu().numpy())[::-1])}

        rrf_scores = {}
        all_indices = set(bm25_ranks.keys()) | set(dense_ranks.keys())

        for idx in all_indices:
            rrf_score = 0.0
            if idx in bm25_ranks:
                rrf_score += 1.0 / (k + bm25_ranks[idx])
            if idx in dense_ranks:
                rrf_score += 1.0 / (k + dense_ranks[idx])
            rrf_scores[idx] = rrf_score

        # Sort by RRF score
        sorted_fused_indices = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        # Map back to original rule indices and get top_k results
        top_k_results = []
        for filtered_idx in sorted_fused_indices[:top_k]:
            original_idx = filtered_original_indices[filtered_idx]
            top_k_results.append(self.rules[original_idx])

        logging.info(f"Returning {len(top_k_results)} combined results.")
        return top_k_results

if __name__ == '__main__':
    # This main block is for demonstration and testing purposes.
    retriever = HybridRetriever()

    if retriever.rules:
        # Example query
        query = "patient goals must be measurable"
        print(f"\n--- Hybrid Search Results for query: '{query}' (PT, Progress Note) ---")

        # Perform the search with filtering
        search_results = retriever.search(query, discipline="pt", doc_type="Progress Note")

        # Print the results
        for i, rule in enumerate(search_results):
            print(f"\nResult {i+1}:")
            print(f"  Title: {rule.issue_title}")
            print(f"  Detail: {rule.issue_detail}")
            print(f"  Discipline: {rule.discipline}")
            print(f"  Doc Type: {rule.document_type}")

        query_2 = "signature of therapist"
        print(f"\n--- Hybrid Search Results for query: '{query_2}' (All disciplines) ---")
        search_results_2 = retriever.search(query_2, discipline="All")
        for i, rule in enumerate(search_results_2):
            print(f"\nResult {i+1}:")
            print(f"  Title: {rule.issue_title}")
            print(f"  Detail: {rule.issue_detail}")
            print(f"  Discipline: {rule.discipline}")
            print(f"  Doc Type: {rule.document_type}")
