from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import faiss
import numpy as np
from huggingface_hub import hf_hub_download
from llama_cpp import Llama
from sentence_transformers import SentenceTransformer

# --- Configuration ---
# Using a small, fast, and effective model for sentence embeddings.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
INDEX_DIR = Path(os.path.expanduser("~")) / "Documents" / "SpecKitData" / "rag_index"
INDEX_FILE = INDEX_DIR / "vector_index.faiss"
DATA_FILE = INDEX_DIR / "document_data.json"


# --- Logging ---
logger = logging.getLogger(__name__)


class LocalRAG:
    """
    A class to manage a local Retrieval-Augmented Generation (RAG) system.
    It uses a sentence transformer for embeddings, FAISS for similarity search,
    and a local LLM for generating responses based on retrieved context.
    This version supports a persistent, growing index.
    """

    def __init__(self, model_repo_id: str, model_filename: str, model: Optional[SentenceTransformer] = None, n_gpu_layers: int = 0):
        """
        Initializes the LocalRAG system.

        Args:
            model_repo_id (str): The Hugging Face repository ID of the GGUF model.
            model_filename (str): The filename of the GGUF model in the repository.
            model (Optional[SentenceTransformer]): An optional pre-loaded sentence transformer model.
            n_gpu_layers (int): Number of layers to offload to GPU. 0 for CPU only.
        """
        self.llm: Optional[Llama] = None
        self.embedding_model: Optional[SentenceTransformer] = model
        self.index: Optional[faiss.Index] = None
        self.documents: List[Dict] = []  # List of dicts with 'text' and 'metadata'

        try:
            # 1. Load the sentence transformer model if not provided
            if self.embedding_model is None:
                logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
                self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
                logger.info("Embedding model loaded successfully.")
            else:
                logger.info("Using pre-loaded sentence transformer model.")

            # 2. Download and load the local LLM
            logger.info(f"Downloading LLM from {model_repo_id}...")
            model_path = hf_hub_download(repo_id=model_repo_id, filename=model_filename)
            logger.info(f"LLM downloaded to: {model_path}")

            self.llm = Llama(
                model_path=model_path,
                n_ctx=4096,  # Context window size
                n_gpu_layers=n_gpu_layers,  # Set to 0 for CPU, or a positive number for GPU layers
                verbose=False,
            )
            logger.info("Local LLM loaded successfully.")

            # 3. Load the persistent index from disk
            self.load_index()

        except Exception as e:
            logger.exception(f"Failed to initialize LocalRAG: {e}")
            # This allows the main application to continue running even if the LLM fails to load.
            self.llm = None
            self.embedding_model = None

    def is_ready(self) -> bool:
        """Check if the RAG system is fully initialized and ready to use."""
        return self.llm is not None and self.embedding_model is not None

    def load_index(self):
        """Loads the FAISS index and document data from disk."""
        if not self.is_ready():
            return
        if INDEX_FILE.exists() and DATA_FILE.exists():
            try:
                logger.info(f"Loading FAISS index from {INDEX_FILE}")
                self.index = faiss.read_index(str(INDEX_FILE))
                logger.info(f"Loading document data from {DATA_FILE}")
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
                logger.info(f"Successfully loaded index with {self.index.ntotal} vectors and {len(self.documents)} documents.")
            except Exception as e:
                logger.exception(f"Failed to load persistent index. Starting fresh. Error: {e}")
                self.index = None
                self.documents = []
        else:
            logger.info("No persistent index found. A new one will be created.")

    def save_index(self):
        """Saves the FAISS index and document data to disk."""
        if not self.is_ready() or self.index is None:
            return
        try:
            INDEX_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"Saving FAISS index to {INDEX_FILE}")
            faiss.write_index(self.index, str(INDEX_FILE))
            logger.info(f"Saving document data to {DATA_FILE}")
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
            logger.info("Successfully saved index and document data.")
        except Exception as e:
            logger.exception(f"Failed to save persistent index: {e}")

    def add_to_index(self, new_docs: List[Dict]):
        """
        Adds new documents to the FAISS index and persists it.

        Args:
            new_docs (List[Dict]): A list of dictionaries, each with 'text' and 'metadata'.
        """
        if not self.is_ready() or not self.embedding_model:
            logger.warning("RAG system is not ready. Cannot add to index.")
            return

        texts = [doc["text"] for doc in new_docs]
        if not texts:
            logger.info("No new texts to add to index.")
            return

        logger.info(f"Adding {len(texts)} new documents to the index.")

        # Generate embeddings for the new text chunks
        new_embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
        new_embeddings = np.array(new_embeddings, dtype=np.float32)

        if self.index is None:
            # Create a new index if it doesn't exist
            embedding_dim = new_embeddings.shape[1]
            self.index = faiss.IndexFlatL2(embedding_dim)
            logger.info(f"Created a new FAISS index with embedding dimension {embedding_dim}.")

        # Add new embeddings to the index
        self.index.add(new_embeddings)
        # Add new document data to our list
        self.documents.extend(new_docs)

        logger.info(f"Index now contains {self.index.ntotal} vectors.")
        self.save_index()

    def search_index(self, query: str, k: int = 5) -> List[Dict]:
        """
        Searches the FAISS index for the most relevant documents.

        Args:
            query (str): The query string.
            k (int): The number of documents to retrieve.

        Returns:
            List[Dict]: A list of the top k most relevant document dictionaries.
        """
        if not self.is_ready() or not self.index or not self.embedding_model:
            logger.warning("RAG system or index is not ready. Cannot perform search.")
            return []

        # Ensure k is not greater than the number of items in the index
        k = min(k, self.index.ntotal)
        if k == 0:
            return []

        query_embedding = self.embedding_model.encode([query])
        _, I = self.index.search(np.array(query_embedding, dtype=np.float32), k)

        retrieved_docs = [self.documents[i] for i in I[0]]
        return retrieved_docs

    def query(self, question: str, context_chunks: List[str], chat_history: List[tuple[str, str]] | None = None) -> str:
        """
        Generates a response from the LLM based on a question and provided context.

        Args:
            question (str): The user's question.
            context_chunks (List[str]): A list of relevant text chunks to use as context.
            chat_history (Optional[List[tuple[str, str]]]): The last N turns of the conversation.

        Returns:
            str: The LLM's generated answer.
        """
        if not self.is_ready() or not self.llm:
            return "The local AI chat is not available. Please check the logs for errors."

        logger.info(f"Received query for generation: {question}")

        # 1. Construct the prompt from the provided context
        # Format the conversational history
        history_str = ""
        if chat_history:
            for sender, message in chat_history[-6:]:
                if sender == 'user':
                    history_str += f"Previous User Question: {message}\n"
                elif sender == 'ai':
                    history_str += f"Your Previous Answer: {message}\n"

        # Format the provided document context
        context_str = ""
        for i, chunk in enumerate(context_chunks):
            context_str += f"BEGININPUT\nBEGINCONTEXT\nsource: document_chunk_{i}\nENDCONTEXT\n{chunk}\nENDINPUT\n"

        # Combine all parts into the final prompt
        prompt = (
            "You are a helpful AI assistant. Answer the user's question based on the provided document context and the recent conversation history.\n\n"
            "--- CONVERSATION HISTORY ---\n"
            f"{history_str}\n"
            "--- DOCUMENT CONTEXT ---\n"
            f"{context_str}\n"
            "--- CURRENT QUESTION ---\n"
            "BEGININSTRUCTION\n"
            f"Based on the provided context and conversation history, answer the following question: {question}\n"
            "ENDINSTRUCTION\n"
        )

        logger.info("Sending prompt to LLM...")

        # 2. Call the LLM to get the answer
        try:
            output = self.llm(prompt, max_tokens=512, stop=["ENDINSTRUCTION"], echo=False)
            answer = output["choices"][0]["text"].strip()
            logger.info(f"LLM generated answer: {answer}")
            return answer
        except Exception as e:
            logger.exception(f"Error during LLM inference: {e}")
            return "An error occurred while generating a response."
