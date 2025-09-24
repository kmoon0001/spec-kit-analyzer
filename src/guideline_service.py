# Python
from __future__ import annotations

# Standard library
import logging
import os
import re
import tempfile
import pickle
from typing import List, Tuple

# Third-party
import pdfplumber
import requests
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import nltk
from src.utils import load_config

# --- NLTK Setup ---
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)

# --- Summarization Pipeline ---
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def summarize_text(text: str, max_length: int = 150, min_length: int = 30) -> str:
    """Generates a summary of the given text."""
    if not text.strip():
        return ""
    try:
        summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        logger.error(f"Error during summarization: {e}")
        return text[:max_length]

logger = logging.getLogger(__name__)

class GuidelineService:
    """
    Manages loading, indexing, and searching of compliance guidelines using a neural retriever.
    Implements caching for the FAISS index and guideline chunks to improve startup time.
    """

    def __init__(self, sources: List[str]):
        """
        Initializes the GuidelineService.
        """
        self.config = load_config()
        model_name = self.config['models']['retriever']

        self.sections_data: list[dict] = []
        self.is_index_ready = False
        self.summary_index = None
        self.detailed_indexes = {}

        self.cache_dir = "data"
        self.summary_index_path = os.path.join(self.cache_dir, "summary.index")
        self.detailed_indexes_path = os.path.join(self.cache_dir, "detailed.pkl")
        self.sections_data_path = os.path.join(self.cache_dir, "sections_data.pkl")
        self.source_paths = sources

        logger.info(f"Loading Sentence Transformer model: {model_name}")
        self.model = SentenceTransformer(model_name)

        self._load_or_build_index()
        logger.info("GuidelineService initialized.")

    def _load_or_build_index(self):
        """Loads the index from cache if valid, otherwise builds it from source."""
        if self._is_cache_valid():
            logger.info("Loading guidelines index from cache...")
            self._load_index_from_cache()
        else:
            logger.info("Cache not found or is invalid. Building index from source...")
            self._build_index_from_sources()
            self._save_index_to_cache()

    def _is_cache_valid(self) -> bool:
        """Checks if the cached hierarchical index and data exist and are up-to-date."""
        if not all(os.path.exists(p) for p in [self.summary_index_path, self.detailed_indexes_path, self.sections_data_path]):
            return False

        cache_mod_time = os.path.getmtime(self.summary_index_path)
        for src_path in self.source_paths:
            if not os.path.exists(src_path) or os.path.getmtime(src_path) > cache_mod_time:
                return False  # Source file is newer than cache
        return True

    def _load_index_from_cache(self):
        """Loads the hierarchical FAISS indexes and section data from disk."""
        try:
            self.summary_index = faiss.read_index(self.summary_index_path)
            with open(self.detailed_indexes_path, 'rb') as f:
                self.detailed_indexes = pickle.load(f)
            with open(self.sections_data_path, 'rb') as f:
                self.sections_data = pickle.load(f)
            self.is_index_ready = True
            logger.info(f"Successfully loaded {len(self.sections_data)} sections and hierarchical FAISS indexes from cache.")
        except Exception as e:
            logger.error(f"Failed to load hierarchical index from cache: {e}")
            self.is_index_ready = False

    def _save_index_to_cache(self):
        """Saves the hierarchical FAISS indexes and section data to disk."""
        if not self.summary_index or not self.detailed_indexes or not self.sections_data:
            logger.warning("Attempted to save cache, but hierarchical index components are missing.")
            return

        try:
            faiss.write_index(self.summary_index, self.summary_index_path)
            with open(self.detailed_indexes_path, 'wb') as f:
                pickle.dump(self.detailed_indexes, f)
            with open(self.sections_data_path, 'wb') as f:
                pickle.dump(self.sections_data, f)
            logger.info(f"Successfully saved hierarchical index and data to '{self.cache_dir}'.")
        except Exception as e:
            logger.error(f"Failed to save hierarchical index to cache: {e}")

    def _build_index_from_sources(self) -> None:
        """Loads guidelines, processes them into a hierarchical structure, and builds FAISS indexes."""
        full_text = ""
        for source_path in self.source_paths:
            if os.path.exists(source_path):
                with open(source_path, 'r', encoding='utf-8') as f:
                    full_text += f.read() + "\n\n"

        if not full_text:
            logger.error("No text could be loaded from sources.")
            return

        # Split the document into large sections using a regex for headers like "1.2 - Title"
        sections = re.split(r'(?=\d{1,2}(?:\.\d{1,3})*\s+-\s+)', full_text)

        logger.info(f"Processing {len(sections)} sections for hierarchical indexing...")

        summaries = []
        for i, section_text in enumerate(sections):
            if not section_text.strip():
                continue

            summary = summarize_text(section_text)
            sentences = nltk.sent_tokenize(section_text)

            self.sections_data.append({
                'id': i,
                'summary': summary,
                'sentences': sentences,
                'source': f"Section {i}"
            })
            summaries.append(summary)

        # Create top-level summary index
        if summaries:
            summary_embeddings = self.model.encode(summaries, convert_to_tensor=False)
            if summary_embeddings.dtype != np.float32:
                summary_embeddings = summary_embeddings.astype(np.float32)

            embedding_dim = summary_embeddings.shape[1]
            self.summary_index = faiss.IndexFlatL2(embedding_dim)
            self.summary_index.add(summary_embeddings)

        # Create detailed index for each section
        for section in self.sections_data:
            if section['sentences']:
                sentence_embeddings = self.model.encode(section['sentences'], convert_to_tensor=False)
                if sentence_embeddings.dtype != np.float32:
                    sentence_embeddings = sentence_embeddings.astype(np.float32)

                embedding_dim = sentence_embeddings.shape[1]
                detailed_index = faiss.IndexFlatL2(embedding_dim)
                detailed_index.add(sentence_embeddings)
                self.detailed_indexes[section['id']] = detailed_index

        self.is_index_ready = True
        logger.info(f"Hierarchical index built for {len(self.sections_data)} sections.")

    def search(self, query: str, top_k: int = None, distance_threshold: float = None) -> List[dict]:
        """
        Performs a hierarchical FAISS similarity search.
        """
        if top_k is None:
            top_k = self.config['retrieval_settings']['similarity_top_k']

        if not self.is_index_ready or not self.summary_index:
            logger.warning("Search called before hierarchical index was ready.")
            return []

        query_embedding = self.model.encode([query])
        if query_embedding.dtype != np.float32:
            query_embedding = query_embedding.astype(np.float32)

        # 1. Search the summary index to find relevant sections
        num_sections_to_search = 3
        distances, summary_indices = self.summary_index.search(query_embedding, num_sections_to_search)

        # 2. Gather all sentences from the top sections
        candidate_sentences = []
        for i in summary_indices[0]:
            if i != -1:
                section = self.sections_data[i]
                candidate_sentences.extend([(sent, section['source']) for sent in section['sentences']])

        if not candidate_sentences:
            return []

        # 3. Encode candidate sentences and perform a final search
        candidate_texts = [s for s, _ in candidate_sentences]
        candidate_embeddings = self.model.encode(candidate_texts)
        if candidate_embeddings.dtype != np.float32:
            candidate_embeddings = candidate_embeddings.astype(np.float32)

        embedding_dim = candidate_embeddings.shape[1]
        final_index = faiss.IndexFlatL2(embedding_dim)
        final_index.add(candidate_embeddings)

        dist, final_indices = final_index.search(query_embedding, top_k)

        # 4. Assemble results
        results = []
        for i, sent_idx in enumerate(final_indices[0]):
            if sent_idx != -1:
                distance = dist[0][i]
                if distance_threshold is None or distance < distance_threshold:
                    text, source = candidate_sentences[sent_idx]
                    results.append({
                        "text": text,
                        "source": source,
                        "distance": distance
                    })

        return results
