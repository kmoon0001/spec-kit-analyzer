import argparse
import os
from src.ingestion import build_sentence_window_index
from src.retrieval import get_query_engine
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# --- Configuration ---
# In a real app, these would be in a config file or environment variables.
# For the purpose of this task, we will use a placeholder OpenAI API Key.
# The user would need to set their actual key as an environment variable.
os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY_HERE"
LLM = OpenAI(model="gpt-3.5-turbo")
EMBED_MODEL = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
INDEX_DIR = "sentence_index"
DOCS_DIR = "data"

def handle_ingest(args):
    """Handles the 'ingest' command."""
    docs_path = args.dir or DOCS_DIR
    if not os.path.exists(docs_path):
        print(f"Error: Document directory not found at '{docs_path}'")
        # Create a dummy data directory for the user
        os.makedirs(docs_path)
        print(f"Created a dummy directory at '{docs_path}'. Please add your documents there and run ingest again.")
        return

    print(f"Starting ingestion from directory: {docs_path}")
    build_sentence_window_index(
        documents_path=docs_path,
        llm=LLM,
        embed_model=EMBED_MODEL,
        save_dir=INDEX_DIR,
    )
    print("Ingestion complete.")

def handle_query(args):
    """Handles the 'query' command."""
    if not args.question:
        print("Error: Please provide a question with the --question flag.")
        return

    print(f"Querying with: '{args.question}'")
    try:
        query_engine = get_query_engine(index_dir=INDEX_DIR)
        response = query_engine.query(args.question)
        print("\n--- Response ---")
        print(response)
        print("\n---")
    except FileNotFoundError as e:
        print(f"Error: {e}. Please run the 'ingest' command first.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def main():
    """Main function to run the command-line interface."""
    parser = argparse.ArgumentParser(description="A command-line interface for a RAG pipeline.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # Subparser for the 'ingest' command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents from a directory into the vector store.")
    ingest_parser.add_argument("--dir", type=str, default=DOCS_DIR, help=f"The directory containing documents to ingest. Defaults to '{DOCS_DIR}'.")
    ingest_parser.set_defaults(func=handle_ingest)

    # Subparser for the 'query' command
    query_parser = subparsers.add_parser("query", help="Ask a question to the indexed documents.")
    query_parser.add_argument("--question", type=str, required=True, help="The question you want to ask.")
    query_parser.set_defaults(func=handle_query)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
