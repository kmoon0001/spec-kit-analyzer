import pickle
import logging
import os
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from rank_bm25 import BM25Okapi
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HybridRetriever:
    def __init__(self, dense_model_name='pritamdeka/S-PubMedBert-MS-MARCO'):
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

        # Get the top_k results from BM25
        top_bm25_indices = np.argsort(bm25_scores)[::-1][:top_k]
        logging.info(f"Top {top_k} BM25 results (indices): {top_bm25_indices}")

        # --- Dense Retriever Search (Semantic) ---
        query_embedding = self.dense_retriever.encode(query, convert_to_tensor=True)

        # We use cosine similarity to find the most similar documents
        cosine_scores = cos_sim(query_embedding, self.corpus_embeddings)[0]

        # Get the top_k results from the dense retriever
        top_dense_indices = np.argsort(cosine_scores.cpu().numpy())[::-1][:top_k]
        logging.info(f"Top {top_k} dense retriever results (indices): {top_dense_indices}")

        # --- Combine Results (Simple Union) ---
        # A simple way to combine the results is to take the union of the two sets of indices.
        # This gives us a list of all unique documents found by either retriever.
        combined_indices = np.union1d(top_bm25_indices, top_dense_indices)
        logging.info(f"Combined unique indices: {combined_indices}")

        # Retrieve the actual documents
        results = [self.corpus[i] for i in combined_indices]

        return results

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
