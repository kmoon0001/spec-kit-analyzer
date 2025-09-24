import pickle
import logging
import os
from sentence_transformers import SentenceTransformer
from sentence_transformers.cross_encoder import CrossEncoder
from sentence_transformers.util import cos_sim
from rank_bm25 import BM25Okapi
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HybridRetriever:
    def __init__(self, dense_model_name='pritamdeka/S-PubMedBert-MS-MARCO', cross_encoder_model_name='cross-encoder/ms-marco-MiniLM-L-6-v2'):
        logging.info("Initializing Hybrid Retriever...")

        # Load the BM25 index and corpus
        logging.info("Loading BM25 index and corpus...")
        with open(os.path.join("data", "bm25_index.pkl"), "rb") as f:
            self.bm25 = pickle.load(f)
        with open(os.path.join("data", "medicare_guideline_corpus.pkl"), "rb") as f:
            self.corpus = pickle.load(f)

        # Load the dense retriever model
        logging.info(f"Loading dense retriever model: {dense_model_name}...")
        self.dense_retriever = SentenceTransformer(dense_model_name)

        # Load the cross-encoder model for re-ranking
        logging.info(f"Loading cross-encoder model: {cross_encoder_model_name}...")
        self.cross_encoder = CrossEncoder(cross_encoder_model_name)

        # Pre-compute embeddings for the entire corpus for the dense retriever
        # This is a one-time operation that will make future searches much faster.
        logging.info("Pre-computing embeddings for the corpus... (This may take a moment)")
        self.corpus_embeddings = self.dense_retriever.encode(self.corpus, convert_to_tensor=True)
        logging.info("Corpus embeddings created successfully.")

        logging.info("Hybrid Retriever initialized successfully.")

    def search(self, query, top_k=5):
        logging.info(f"\nPerforming hybrid search for query: '{query}'")

        # --- BM25 Search (Keyword-based) ---
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)

        # Get all scores from BM25 and rank the documents
        bm25_ranked_indices = np.argsort(bm25_scores)[::-1]
        logging.info(f"Top 5 BM25 results (indices): {bm25_ranked_indices[:5]}")

        # --- Dense Retriever Search (Semantic) ---
        query_embedding = self.dense_retriever.encode(query, convert_to_tensor=True)

        # We use cosine similarity to find the most similar documents
        cosine_scores = cos_sim(query_embedding, self.corpus_embeddings)[0]

        # Get all scores from dense retriever and rank the documents
        dense_ranked_indices = np.argsort(cosine_scores.cpu().numpy())[::-1]
        logging.info(f"Top 5 dense retriever results (indices): {dense_ranked_indices[:5]}")

        # --- Fuse Results with Reciprocal Rank Fusion (RRF) ---
        fused_indices = self._rrf_fuse([bm25_ranked_indices, dense_ranked_indices])

        # We'll take the top 2*k results from the fused list to feed into the cross-encoder
        combined_indices = fused_indices[:top_k*2]
        logging.info(f"Combined and fused unique indices: {combined_indices}")

        # Retrieve the actual documents
        initial_results = [self.corpus[i] for i in combined_indices]

        # --- Re-ranking with Cross-Encoder ---
        logging.info(f"Re-ranking {len(initial_results)} documents with cross-encoder...")
        # Create pairs of (query, document) for the cross-encoder
        cross_encoder_input = [[query, doc] for doc in initial_results]

        # Get scores from the cross-encoder
        cross_encoder_scores = self.cross_encoder.predict(cross_encoder_input)

        # Sort the initial results based on the cross-encoder scores
        reranked_results = [doc for _, doc in sorted(zip(cross_encoder_scores, initial_results), reverse=True)]

        logging.info("Re-ranking complete.")

        return reranked_results[:top_k]

    def _rrf_fuse(self, ranked_lists, k=60):
        """
        Fuses multiple ranked lists using Reciprocal Rank Fusion (RRF).
        :param ranked_lists: A list of lists, where each inner list is a ranked list of document indices.
        :param k: The ranking constant for RRF.
        :return: A single fused and ranked list of document indices.
        """
        rrf_scores = {}

        # Calculate RRF scores
        for ranked_list in ranked_lists:
            for rank, doc_id in enumerate(ranked_list):
                if doc_id not in rrf_scores:
                    rrf_scores[doc_id] = 0
                rrf_scores[doc_id] += 1 / (k + rank)

        # Sort documents by their RRF score in descending order
        sorted_docs = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        return sorted_docs

if __name__ == '__main__':
    retriever = HybridRetriever()

    # Example query
    query = "skilled nursing facility level of care"

    # Perform the search
    search_results = retriever.search(query)

    # Print the results
    print("\n--- Hybrid Search Results ---")
    for i, result in enumerate(search_results):
        print(f"Result {i+1}:\n{result}\n")

    query_2 = "payment bans on new admissions"
    search_results_2 = retriever.search(query_2)
    print("\n--- Hybrid Search Results ---")
    for i, result in enumerate(search_results_2):
        print(f"Result {i+1}:\n{result}\n")
