import logging
import re

import nltk  # type: ignore[import-untyped]

# Set up logging
logger = logging.getLogger(__name__)

# --- NLTK Setup ---
try:
    nltk.data.find("tokenizers/punkt")
    PUNKT_AVAILABLE = True
except LookupError:
    logger.warning(
        "NLTK 'punkt' tokenizer data is not available. Falling back to a simple sentence splitter."
    )
    PUNKT_AVAILABLE = False


def _fallback_sentence_split(text: str) -> list[str]:
    """Lightweight sentence splitter used when NLTK punkt data is unavailable."""

    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def sentence_window_chunker(text: str, window_size: int = 1, metadata: dict | None = None):
    """Splits text into sentences and creates chunks with a sliding window of context.

    Each chunk dictionary will contain the target sentence and the context window
    as a single string.

    Args:
        text (str): The input text.
        window_size (int): The number of sentences to include before and after the target sentence.

    Returns:
        list[dict]: A list of chunks, where each chunk is a dictionary containing:
                    - 'sentence': The target sentence.
                    - 'window': The target sentence plus its surrounding context sentences.
                    - 'metadata': An empty dictionary for now.

    """
    if not text:
        return []

    if PUNKT_AVAILABLE:
        try:
            sentences = nltk.sent_tokenize(text)
        except LookupError:
            logger.warning("Falling back to simple sentence splitting due to missing punkt data.")
            sentences = _fallback_sentence_split(text)
    else:
        sentences = _fallback_sentence_split(text)
    chunks = []

    for i, sentence in enumerate(sentences):
        # Define the window boundaries
        start_index = max(0, i - window_size)
        end_index = min(len(sentences), i + 1 + window_size)

        # Create the window of sentences
        window_sentences = sentences[start_index:end_index]
        window_text = " ".join(window_sentences)

        chunk_metadata = metadata.copy() if metadata else {}
        chunk = {
            "sentence": sentence,
            "window": window_text,
            "metadata": chunk_metadata,
        }
        chunks.append(chunk)

    return chunks
