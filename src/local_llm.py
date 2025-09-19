from __future__ import annotations

import logging
from typing import Dict, List, Optional

import faiss
import numpy as np
from huggingface_hub import hf_hub_download
from llama_cpp import Llama
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
logger = logging.getLogger(__name__)

class LocalRAG:
    """
    A class to manage a local Retrieval-Augmented Generation (RAG) system.
    This version uses an in-memory index for the current session only.
    """

    def __init__(self, model_repo_id: str, model_filename: str, model: Optional[SentenceTransformer] = None, n_gpu_layers: int = 0):
        self.llm: Optional[Llama] = None
        self.embedding_model: Optional[SentenceTransformer] = model
        self.index: Optional[faiss.Index] = None
        self.documents_with_sources: List[tuple[str, str]] = []

        try:
            if self.embedding_model is None:
                logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
                self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
                logger.info("Embedding model loaded successfully.")
            else:
                logger.info("Using pre-loaded sentence transformer model.")

            logger.info(f"Downloading LLM from {model_repo_id}...")
            model_path = hf_hub_download(repo_id=model_repo_id, filename=model_filename)
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
        return self.llm is not None and self.embedding_model is not None

    def create_index(self, docs_with_sources: List[tuple[str, str]]):
        """
        Creates a new in-memory FAISS index from a list of documents with sources.
        This overwrites any existing index.
        """
        if not self.is_ready() or not self.embedding_model:
            logger.warning("RAG system is not ready. Cannot create index.")
            return

        self.documents_with_sources = docs_with_sources
        if not self.documents_with_sources:
            self.index = None
            return

        logger.info(f"Creating new in-memory index for {len(self.documents_with_sources)} documents.")

        documents = [doc for doc, src in self.documents_with_sources]

        embeddings = self.embedding_model.encode(documents, convert_to_tensor=False)
        embeddings = np.array(embeddings, dtype=np.float32)

        embedding_dim = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(embedding_dim)
        self.index.add(embeddings)
        logger.info(f"In-memory index created with {self.index.ntotal} vectors.")

    def search_index(self, query: str, k: int = 3) -> List[tuple[str, str]]:
        """
        Searches the in-memory FAISS index for the most relevant documents.
        """
        if not self.is_ready() or not self.index or not self.embedding_model:
            logger.warning("RAG system or index is not ready. Cannot perform search.")
            return []

        k = min(k, self.index.ntotal)
        if k == 0:
            return []

        query_embedding = self.embedding_model.encode([query])
        _, I = self.index.search(np.array(query_embedding, dtype=np.float32), k)

        return [self.documents_with_sources[i] for i in I[0]]

    def query(self, question: str, context_chunks: List[tuple[str, str]], chat_history: List[tuple[str, str, list[str]]] | None = None) -> tuple[str, list[tuple[str, str]]]:
        if not self.is_ready() or not self.llm:
            return "The local AI chat is not available. Please check the logs for errors.", []

        logger.info(f"Received query for generation: {question}")

        history_str = ""
        if chat_history:
            for sender, message, sources in chat_history[-6:]:
                if sender == 'user':
                    history_str += f"Previous User Question: {message}\n"
                elif sender == 'ai':
                    history_str += f"Your Previous Answer: {message}\n"

        context_str = ""
        for i, (chunk, source) in enumerate(context_chunks):
            # Use a numeric index for the source, which is easier for the LLM to use
            context_str += f"BEGININPUT\nBEGINCONTEXT\nsource_index: {i+1}\nENDCONTEXT\n{chunk}\nENDINPUT\n"

        prompt = (
            "You are a helpful AI assistant. Answer the user's question based on the provided document context and the recent conversation history. "
            "When you use information from the context, you must cite the source by including the source_index in brackets, like this: [1]. "
            "You can cite multiple sources like this: [1, 2].\n\n"
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

        try:
            output = self.llm(prompt, max_tokens=512, stop=["ENDINSTRUCTION"], echo=False)
            answer = output["choices"][0]["text"].strip()

            logger.info(f"LLM generated answer: {answer}")
            return answer, context_chunks
        except Exception as e:
            logger.exception(f"Error during LLM inference: {e}")
            return "An error occurred while generating a response.", []
