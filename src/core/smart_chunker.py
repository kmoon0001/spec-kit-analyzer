import nltk
import logging

# Set up logging
logger = logging.getLogger(__name__)

# --- NLTK Setup ---
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    logger.info("NLTK 'punkt' tokenizer not found. Downloading...")
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    logger.info("'punkt' tokenizer downloaded successfully.")

def sentence_window_chunker(text: str, window_size: int = 1, metadata: dict | None = None):
    """
    Splits text into sentences and creates chunks with a sliding window of context.

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

    sentences = nltk.sent_tokenize(text)
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
            "metadata": chunk_metadata
        }
        chunks.append(chunk)

    return chunks
