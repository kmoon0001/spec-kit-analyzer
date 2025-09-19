import os
from llama_index.core import load_index_from_storage, Settings, StorageContext
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI # Placeholder

from llama_index.core.llms import LLM

def get_query_engine(
    index_dir: str = "sentence_index",
    llm: LLM = None,
    rerank_top_n: int = 2,
    similarity_top_k: int = 6,
):
    """
    Loads a LlamaIndex and builds a query engine with a reranker.

    Args:
        index_dir (str): The directory where the index is saved.
        llm (LLM): The language model to use. If None, defaults to OpenAI.
        rerank_top_n (int): The number of documents to return after reranking.
        similarity_top_k (int): The number of documents to retrieve initially.

    Returns:
        A LlamaIndex query engine.
    """
    if not os.path.exists(index_dir):
        raise FileNotFoundError(f"Index directory not found at {index_dir}. Please build the index first.")

    # Set up the global settings to match the ingestion settings
    # In a larger app, this would be handled by a config file.
    Settings.llm = llm or OpenAI(model="gpt-3.5-turbo")
    Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Load the index from disk
    storage_context = StorageContext.from_defaults(persist_dir=index_dir)
    index = load_index_from_storage(storage_context)

    # The reranker will use a cross-encoder to re-order the retrieved documents
    # for higher relevance.
    reranker = SentenceTransformerRerank(
        model="cross-encoder/ms-marco-MiniLM-L-6-v2", top_n=rerank_top_n
    )

    query_engine = index.as_query_engine(
        similarity_top_k=similarity_top_k,
        node_postprocessors=[reranker],
    )

    return query_engine

# This file is intended to be used as a module.
# Example usage will be demonstrated in the main application script and tests.
