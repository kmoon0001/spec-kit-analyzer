from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional

import faiss
import numpy as np
from huggingface_hub import hf_hub_download
from llama_cpp import Llama
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- Configuration ---
# Using a small, fast, and effective model for sentence embeddings.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# --- Logging ---
logger = logging.getLogger(__name__)


class LocalRAG:
    """
    A class to manage a local Retrieval-Augmented Generation (RAG) system.
    It uses a sentence transformer for embeddings, FAISS for similarity search,
    and a local LLM for generating responses based on retrieved context.
    """

    def __init__(
        self,
        model_repo_id: str,
        model_filename: str,
        model: Optional[SentenceTransformer] = None,
        n_gpu_layers: int = 0
    ):
        """
        Initializes the LocalRAG system.

        Args:
            model_repo_id (str): The Hugging Face repository ID of the GGUF model.
            model_filename (str): The filename of the GGUF model in the repository.
            model (Optional[SentenceTransformer]): An optional pre-loaded
                                                   sentence transformer model.
            n_gpu_layers (int): Number of layers to offload to GPU. 0 for CPU only.
        """
        self.llm: Optional[Llama] = None
        self.embedding_model: Optional[SentenceTransformer] = model
        self.index: Optional[faiss.Index] = None
        self.text_chunks: List[str] = []

        # Attributes for keyword search
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None

        try:
            if self.embedding_model is None:
                logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
                self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
                logger.info("Embedding model loaded successfully.")
            else:
                logger.info("Using pre-loaded sentence transformer model.")

            # 2. Download and load the local LLM
            logger.info(f"Downloading LLM from {model_repo_id}...")
            model_path = hf_hub_download(
                repo_id=model_repo_id, filename=model_filename
            )
            logger.info(f"LLM downloaded to: {model_path}")

            self.llm = Llama(
                model_path=model_path,
                n_ctx=4096,
                n_gpu_layers=n_gpu_layers,
                verbose=False,
            )
            logger.info("Local LLM loaded successfully.")

        except Exception as e:
            logger.exception(f"Failed to initialize LocalRAG: {e}")
            self.llm = None
            self.embedding_model = None

    def is_ready(self) -> bool:
        """Check if the RAG system is fully initialized and ready to use."""
        return self.llm is not None and self.embedding_model is not None

    def create_index(self, texts: List[str]):
        """
        Creates a FAISS index and a TF-IDF matrix from a list of text chunks.

        Args:
            texts (List[str]): A list of strings, where each string is a
                               chunk of text.
        """
        if not self.is_ready() or not self.embedding_model:
            logger.warning("RAG system is not ready. Cannot create index.")
            return

        logger.info(f"Creating FAISS index for {len(texts)} text chunks.")
        self.text_chunks = texts

        embeddings = self.embedding_model.encode(
            texts, convert_to_tensor=False
        )
        embedding_dim = embeddings.shape[1]

        # Create a FAISS index for semantic search
        self.index = faiss.IndexFlatL2(embedding_dim)
        self.index.add(np.array(embeddings, dtype=np.float32))
        logger.info("FAISS index created successfully.")

        # Create a TF-IDF matrix for keyword search
        logger.info("Creating TF-IDF index for keyword search.")
        self.tfidf_vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
        logger.info("TF-IDF index created successfully.")

    def search_index(self, query: str, k: int = 5) -> List[str]:
        """
        Performs a hybrid search using both semantic and keyword search,
        then merges the results using Reciprocal Rank Fusion (RRF).

        Args:
            query (str): The query string.
            k (int): The number of final chunks to retrieve.

        Returns:
            List[str]: A list of the top k most relevant text chunks.
        """
        if not self.is_ready() or not self.embedding_model:
            logger.warning("RAG system is not ready. Cannot perform search.")
            return []

        # --- 1. Semantic (Vector) Search ---
        semantic_results_indices = []
        if self.index:
            query_embedding = self.embedding_model.encode([query])
            _, top_k_indices = self.index.search(np.array(query_embedding, dtype=np.float32), k * 2)
            semantic_results_indices = top_k_indices[0]

        # --- 2. Keyword (TF-IDF) Search ---
        keyword_results_indices = []
        if self.tfidf_vectorizer and self.tfidf_matrix is not None:
            query_vec = self.tfidf_vectorizer.transform([query])
            similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            top_k_indices = similarities.argsort()[::-1][:k * 2]
            keyword_results_indices = top_k_indices

        # --- 3. Reciprocal Rank Fusion (RRF) ---
        fused_scores = {}
        rrf_k = 60  # RRF constant

        for i, doc_index in enumerate(semantic_results_indices):
            if doc_index not in fused_scores:
                fused_scores[doc_index] = 0
            fused_scores[doc_index] += 1 / (rrf_k + i + 1)

        for i, doc_index in enumerate(keyword_results_indices):
            if doc_index not in fused_scores:
                fused_scores[doc_index] = 0
            fused_scores[doc_index] += 1 / (rrf_k + i + 1)

        # Sort by fused score
        sorted_doc_indices = sorted(fused_scores.keys(), key=lambda idx: fused_scores[idx], reverse=True)

        # Get the final documents
        final_results = [self.text_chunks[i] for i in sorted_doc_indices[:k]]

        return final_results

    def query(self, question: str, k: int = 3, chat_history: List[tuple[str, str]] | None = None) -> str:
        """
        Queries the RAG system, now with conversational history.

        Args:
            question (str): The user's question.
            k (int): The number of relevant text chunks to retrieve.
            chat_history (Optional[List[tuple[str, str]]]): The last N turns of the conversation.

        Returns:
            str: The LLM's generated answer.
        """
        if not self.is_ready() or not self.index or not self.embedding_model or not self.llm:
            return "The local AI chat is not available. Please check the logs for errors."

        logger.info(f"Received query: {question}")
        # 1. Find relevant text chunks from the FAISS index
        retrieved_chunks = self.search_index(question, k=k)

        # 2. Construct the prompt
        history_str = ""
        if chat_history:
            for sender, message in chat_history[-6:]:
                if sender == 'user':
                    history_str += f"Previous User Question: {message}\n"
                elif sender == 'ai':
                    history_str += f"Your Previous Answer: {message}\n"

        # Format the retrieved document context
        context_str = ""
        for i, chunk in enumerate(retrieved_chunks):
            context_str += f"BEGININPUT\nBEGINCONTEXT\nsource: " \
                           f"document_chunk_{i}\nENDCONTEXT\n{chunk}\nENDINPUT\n"

        # Combine all parts into the final prompt
        prompt = (
            "You are a helpful AI assistant. Answer the user's question based "
            "on the provided document context and the recent conversation "
            "history.\n\n"
            "--- CONVERSATION HISTORY ---\n"
            f"{history_str}\n"
            "--- DOCUMENT CONTEXT ---\n"
            f"{context_str}\n"
            "--- CURRENT QUESTION ---\n"
            "BEGININSTRUCTION\n"
            "Based on the provided context and conversation history, answer "
            f"the following question: {question}\n"
            "ENDINSTRUCTION\n"
        )

        logger.info("Sending prompt to LLM...")

        try:
            output = self.llm(
                prompt, max_tokens=512, stop=["ENDINSTRUCTION"], echo=False
            )
            answer = output["choices"][0]["text"].strip()
            logger.info(f"LLM generated answer: {answer}")
            return answer
        except Exception as e:
            logger.exception(f"Error during LLM inference: {e}")
            return "An error occurred while generating a response."