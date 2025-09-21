import os
from langchain.schema import Document # This might be implicitly needed by LlamaIndex, keeping for now.

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceWindowNodeParser
from llama_index.llms.openai import OpenAI # Placeholder, can be swapped
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

def build_sentence_window_index(
    documents_path: str,
    llm,
    embed_model,
    save_dir: str,
):
    """
    Builds a LlamaIndex VectorStoreIndex with a SentenceWindowNodeParser.

    Args:
        documents_path (str): Path to the directory with documents.
        llm: The language model to use.
        embed_model: The embedding model to use.
        save_dir (str): Directory to save the index.
    """
    documents = SimpleDirectoryReader(documents_path).load_data()

    node_parser = SentenceWindowNodeParser.from_defaults(
        window_size=3,
        window_metadata_key="window",
        original_text_metadata_key="original_text",
    )

    # Create the index from the documents
    # The models are passed directly to the service context
    print("Creating sentence window index...")
    sentence_index = VectorStoreIndex.from_documents(
        documents,
        llm=llm,
        embed_model=embed_model,
        transformations=[node_parser],
    )

    # Persist the index to disk
    sentence_index.storage_context.persist(persist_dir=save_dir)
    print(f"Sentence window index saved to {save_dir}")
    return sentence_index

# This file is intended to be used as a module.
# Example usage will be demonstrated in the main application script and tests.
