import os
import logging
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF, RDFS
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HybridRetriever:
    """
    A retriever that uses a hybrid of keyword-based (BM25) and semantic (dense)
    search to find relevant compliance guidelines from .ttl files.
    """
    def __init__(self, dense_model_name='pritamdeka/S-PubMedBert-MS-MARCO'):
        logging.info("Initializing Hybrid Retriever...")

        self.guidelines = self._load_guidelines_from_ttl()
        if not self.guidelines:
            logging.warning("No guidelines loaded. Retriever will be empty.")
            self.corpus = []
            self.bm25 = None
            self.dense_retriever = None
            self.corpus_embeddings = None
            return

        self.corpus = [
            f"{g['label']}. {g['comment']}"
            for g in self.guidelines
        ]
        logging.info(f"Created a corpus with {len(self.corpus)} guidelines.")

        tokenized_corpus = [doc.lower().split() for doc in self.corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)

        logging.info(f"Loading dense retriever model: {dense_model_name}...")
        self.dense_retriever = SentenceTransformer(dense_model_name)
        self.corpus_embeddings = self.dense_retriever.encode(self.corpus, convert_to_tensor=True)
        logging.info("Hybrid Retriever initialized successfully.")

    def _load_guidelines_from_ttl(self) -> List[Dict]:
        """Loads all compliance guidelines from .ttl files in the resources directory."""
        guidelines = []
        resources_path = os.path.join(os.path.dirname(__file__), '..', 'resources')
        if not os.path.exists(resources_path):
            logging.error(f"Resources directory not found at: {resources_path}")
            return []

        for filename in os.listdir(resources_path):
            if filename.endswith(".ttl"):
                filepath = os.path.join(resources_path, filename)
                try:
                    g = Graph()
                    g.parse(filepath, format="turtle")
                    for s, p, o in g.triples((None, RDF.type, RDFS.Class)):
                        label = g.value(s, RDFS.label)
                        comment = g.value(s, RDFS.comment)
                        if label and comment:
                            guidelines.append({"label": str(label), "comment": str(comment)})
                except Exception as e:
                    logging.error(f"Failed to parse TTL file {filename}: {e}")

        logging.info(f"Loaded {len(guidelines)} guidelines from TTL files.")
        return guidelines

    def search(self, query: str, top_k: int = 5) -> List[str]:
        """
        Performs a hybrid search and returns the top_k relevant guideline strings.
        """
        if not self.guidelines:
            return []

        # --- BM25 Search (Keyword-based) ---
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)

        # --- Dense Retriever Search (Semantic) ---
        query_embedding = self.dense_retriever.encode(query, convert_to_tensor=True)
        cosine_scores = cos_sim(query_embedding, self.corpus_embeddings)[0].cpu().numpy()

        # --- Reciprocal Rank Fusion (RRF) for combining results ---
        k = 60 # RRF k parameter
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

        sorted_fused_indices = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        # Return the guideline strings
        top_k_strings = [self.corpus[i] for i in sorted_fused_indices[:top_k]]
        return top_k_strings