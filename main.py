import argparse
import os
import yaml
from src.ingestion import build_sentence_window_index
from src.retrieval import get_query_engine
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

def load_config(config_path="config.yaml"):
    """Loads the YAML configuration file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def handle_ingest(args, config):
    """Handles the 'ingest' command."""
    docs_path = args.dir or config["paths"]["docs_dir"]
    if not os.path.exists(docs_path):
        print(f"Error: Document directory not found at '{docs_path}'")
        os.makedirs(docs_path)
        print(f"Created a dummy directory at '{docs_path}'. Please add your documents there and run ingest again.")
        return

    print(f"Starting ingestion from directory: {docs_path}")

    # Set up models from config
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "YOUR_API_KEY_HERE")
    llm = OpenAI(model=config["models"]["llm"]["model_name"])
    embed_model = HuggingFaceEmbedding(model_name=config["models"]["embed_model"]["model_name"])

    build_sentence_window_index(
        documents_path=docs_path,
        llm=llm,
        embed_model=embed_model,
        save_dir=config["paths"]["index_dir"],
    )
    print("Ingestion complete.")

def handle_query(args, config):
    """Handles the 'query' command."""
    if not args.question:
        print("Error: Please provide a question with the --question flag.")
        return

    print(f"Querying with: '{args.question}'")
    try:
        # Set up models from config for retrieval
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "YOUR_API_KEY_HERE")
        llm = OpenAI(model=config["models"]["llm"]["model_name"])

        query_engine = get_query_engine(
            index_dir=config["paths"]["index_dir"],
            llm=llm,
            embed_model_name=config["models"]["embed_model"]["model_name"],
            reranker_config=config["models"]["reranker"],
            retrieval_config=config["retrieval"],
        )
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
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to the configuration file.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # Load configuration to get default values
    # This is a bit of a trick to show defaults in help messages
    try:
        config = load_config()
    except FileNotFoundError:
        config = {"paths": {"docs_dir": "data"}} # default fallback

    # Subparser for the 'ingest' command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents from a directory into the vector store.")
    ingest_parser.add_argument(
        "--dir",
        type=str,
        default=config["paths"]["docs_dir"],
        help=f"The directory containing documents to ingest. Defaults to '{config['paths']['docs_dir']}'."
    )
    ingest_parser.set_defaults(func=handle_ingest)

    # Subparser for the 'query' command
    query_parser = subparsers.add_parser("query", help="Ask a question to the indexed documents.")
    query_parser.add_argument("--question", type=str, required=True, help="The question you want to ask.")
    query_parser.set_defaults(func=handle_query)

    args = parser.parse_args()

    # Load the config specified by the user, or the default
    final_config = load_config(args.config)

    # Call the appropriate handler with the args and config
    args.func(args, final_config)

if __name__ == "__main__":
    main()
