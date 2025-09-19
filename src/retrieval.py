import os
from llama_index.core import load_index_from_storage, Settings, StorageContext
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import TransformRetriever
from llama_index.core.indices.query.query_transform import HyDEQueryTransform
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI # Placeholder

from llama_index.core.llms import LLM

def get_query_engine(
    index_dir: str,
    llm: LLM,
    embed_model_name: str,
    reranker_config: dict,
    retrieval_config: dict,
):
    """
    Loads a LlamaIndex and builds a query engine with HyDE transformation and a reranker.

    Args:
        index_dir (str): The directory where the index is saved.
        llm (LLM): The language model to use.
        embed_model_name (str): The name of the embedding model to use.
        reranker_config (dict): Configuration for the reranker model.
        retrieval_config (dict): Configuration for the retriever.

    Returns:
        A LlamaIndex query engine.
    """
    if not os.path.exists(index_dir):
        raise FileNotFoundError(f"Index directory not found at {index_dir}. Please build the index first.")

    # Set the models in the global settings before loading
    Settings.llm = llm
    Settings.embed_model = HuggingFaceEmbedding(model_name=embed_model_name)

    # Load the index from disk. It will now use the models from Settings.
    storage_context = StorageContext.from_defaults(persist_dir=index_dir)
    index = load_index_from_storage(storage_context)

    # 1. Create the base retriever
    base_retriever = index.as_retriever(similarity_top_k=retrieval_config["similarity_top_k"])

    # 2. Create the HyDE query transform, passing in the LLM
    hyde_transform = HyDEQueryTransform(include_original=True, llm=llm)
    hyde_retriever = TransformRetriever(
        retriever=base_retriever, query_transform=hyde_transform
    )

    # 3. Create the reranker from config
    reranker = SentenceTransformerRerank(
        model=reranker_config["model_name"], top_n=retrieval_config["rerank_top_n"]
    )

    # 4. Build the query engine with the transformed retriever and reranker
    query_engine = RetrieverQueryEngine.from_args(
        retriever=hyde_retriever,
        node_postprocessors=[reranker],
        llm=llm,
    )

    return query_engine

# This file is intended to be used as a module.
# Example usage will be demonstrated in the main application script and tests.
