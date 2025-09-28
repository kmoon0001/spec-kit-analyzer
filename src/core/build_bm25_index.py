import re
import pickle
from rank_bm25 import BM25Okapi  # type: ignore


def preprocess_text(text):
    """
    Simple text preprocessing: lowercase, remove non-alphanumeric characters,
    and split into words.
    """
    text = re.sub(r"[^\w\s]", "", text)  # Remove punctuation
    return text.lower().split()


def create_bm25_index():
    """
    Reads the Medicare Benefit Policy Manual, creates a BM25 index,
    and saves the index and the text corpus to disk.
    """
    print("Reading Medicare guideline text...")
    with open(
        "medicare_benefit_policy_manual_chapter_8.txt", "r", encoding="utf-8"
    ) as f:
        text = f.read()

    # New regex to split by section headers, not dependent on newlines.
    # We split on the pattern: (number) - (Title)
    # The positive lookahead `(?=...)` keeps the delimiter (the section header) as part of the next section.
    sections = re.split(r"(?=\d{1,2}(?:\.\d{1,3})*\s+-\s+)", text)

    # The first element might be the title or empty, so we'll handle that.
    corpus = []
    if sections:
        # The first split might be the document title before the first section
        # Let's treat the Table of Contents and the first section separately.
        title_and_toc = sections[0]
        # We can split the ToC into its own lines for better granularity
        toc_lines = [line.strip() for line in title_and_toc.split("  ") if line.strip()]
        corpus.extend(toc_lines)

        # Add the rest of the sections
        corpus.extend([s.strip() for s in sections[1:] if s.strip()])

    print(f"Split text into {len(corpus)} documents.")

    if len(corpus) <= 1:
        print(
            "Error: The document was not split into multiple sections. The index will not be effective."
        )
        return  # Exit if we still can't split the document

    # Preprocess and tokenize the corpus
    print("Tokenizing documents...")
    tokenized_corpus = [preprocess_text(doc) for doc in corpus]

    # Create the BM25 index
    print("Creating BM25 index...")
    bm25 = BM25Okapi(tokenized_corpus)

    # Save the index and the original corpus to disk
    print("Saving index and corpus to disk...")
    with open("bm25_index.pkl", "wb") as f:
        pickle.dump(bm25, f)

    with open("medicare_guideline_corpus.pkl", "wb") as f:
        pickle.dump(corpus, f)

    print("BM25 index created and saved successfully to 'bm25_index.pkl'.")
    print("Text corpus saved successfully to 'medicare_guideline_corpus.pkl'.")


if __name__ == "__main__":
    create_bm25_index()
