#!/bin/sh

# This script is the entrypoint for the Docker container.
# It performs any necessary setup tasks before executing the main command.

echo "--- Running Entrypoint Script ---"

# Check if the vector store has already been built.
# If not, run the build script.
if [ ! -d "/app/vector_store" ]; then
  echo "Vector store not found. Building now..."
  python build_vector_store.py
else
  echo "Vector store already exists. Skipping build."
fi

# Execute the command passed to this script (e.g., gunicorn or celery).
# This allows the same entrypoint to be used for both the api and worker services.
exec "$@"
