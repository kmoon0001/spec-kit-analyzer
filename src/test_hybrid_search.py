import unittest
from unittest.mock import patch, MagicMock
import numpy as np

# Mock the heavyweight dependencies before they are imported by local_llm
mock_llama = MagicMock()
mock_sentence_transformer = MagicMock()
mock_hf_hub_download = MagicMock(return_value="mock_path")

# These modules are mocked, so the original classes are replaced with MagicMock
modules = {
    'llama_cpp': MagicMock(Llama=mock_llama),
    'sentence_transformers': MagicMock(SentenceTransformer=mock_sentence_transformer),
    'huggingface_hub': MagicMock(hf_hub_download=mock_hf_hub_download),
    'faiss': MagicMock()
}

with patch.dict('sys.modules', modules):
    from src.local_llm import LocalRAG

class TestHybridSearchInLocalRAG(unittest.TestCase):

    @patch('src.local_llm.SentenceTransformer')
    @patch('src.local_llm.Llama')
    @patch('src.local_llm.hf_hub_download')
    def setUp(self, mock_hf_hub, mock_llama_cls, mock_st_cls):
        """Set up a LocalRAG instance with mock data for testing."""

        # Configure mocks
        self.mock_st_instance = mock_st_cls.return_value
        self.mock_llama_instance = mock_llama_cls.return_value

        # Instantiate LocalRAG - this will use the mocked classes
        self.rag = LocalRAG(model_repo_id="test-repo", model_filename="test-model.gguf", model=self.mock_st_instance)
        self.rag.llm = self.mock_llama_instance # Ensure LLM is mocked
        self.rag.embedding_model = self.mock_st_instance

        self.documents = [
            "The quick brown fox jumps over the lazy dog.",
            "A fast brown fox leaps over a sleepy dog.",
            "Never jump over the lazy dog quickly.",
            "The sun shines brightly in the summer.",
            "A lazy cat sleeps in the sun."
        ]

        # Simulate the index creation process
        # 1. Mock sentence embeddings
        mock_embeddings = np.random.rand(len(self.documents), 384).astype('float32')
        self.mock_st_instance.encode.return_value = mock_embeddings

        # 2. Mock FAISS index
        self.mock_faiss_index = MagicMock()
        self.rag.index = self.mock_faiss_index

        # 3. Create the real TF-IDF matrix
        self.rag.create_index(self.documents)

        # Ensure the documents are stored
        self.rag.text_chunks = self.documents


    def test_search_integration(self):
        """Test the main search_index method which integrates keyword and semantic searches."""
        query = "a quick dog"
        top_k = 3

        # --- Mock the results from the two search types ---

        # 1. Mock FAISS search results (semantic)
        # Let's say semantic search ranks doc 1, then 0
        semantic_indices = np.array([[1, 0, 2, 3, 4]])
        self.rag.index.search.return_value = (None, semantic_indices)

        # 2. Mock SentenceTransformer for the query
        query_embedding = np.random.rand(1, 384).astype('float32')
        self.rag.embedding_model.encode.return_value = query_embedding

        # --- Execute the search ---
        results = self.rag.search_index(query, k=top_k)

        # --- Assertions ---
        # Keyword search for "a quick dog" should strongly prefer doc 0, then 2.
        # Semantic search is mocked to prefer doc 1, then 0.
        # RRF should combine these.
        #
        # Expected RRF Ranking:
        # Keyword:  doc 0 (rank 0), doc 2 (rank 1)
        # Semantic: doc 1 (rank 0), doc 0 (rank 1)
        #
        # RRF Scores (k=60):
        # Doc 0: (1/61) + (1/61) = 0.0327
        # Doc 1: (1/61) = 0.01639
        # Doc 2: (1/62) = 0.01612
        #
        # Whoops, let's re-calculate RRF based on the implementation
        # score = 1 / (k + rank + 1)
        # Doc 0: (1 / (60 + 0 + 1)) [keyword] + (1 / (60 + 1 + 1)) [semantic] = 1/61 + 1/62 = 0.01639 + 0.01612 = 0.03251
        # Doc 1: (1 / (60 + 0 + 1)) [semantic] = 1/61 = 0.01639
        # Doc 2: (1 / (60 + 1 + 1)) [keyword] = 1/62 = 0.01612
        #
        # Expected order: Doc 0, Doc 1, Doc 2

        self.assertEqual(len(results), top_k)
        self.assertEqual(results[0], self.documents[0]) # "The quick brown fox..."
        self.assertEqual(results[1], self.documents[1]) # "A fast brown fox..."
        self.assertEqual(results[2], self.documents[2]) # "Never jump over..."

    def test_search_with_no_semantic_results(self):
        """Test search when FAISS returns no results."""
        query = "quick dog"
        top_k = 2

        # Mock FAISS to return empty results
        self.rag.index.search.return_value = (None, np.array([[]]))
        self.rag.embedding_model.encode.return_value = np.random.rand(1, 384).astype('float32')

        results = self.rag.search_index(query, k=top_k)

        # Should fall back to pure keyword search.
        # Keyword search for "quick dog" prefers doc 0, then 2.
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], self.documents[0])
        self.assertEqual(results[1], self.documents[2])

    def test_search_with_no_keyword_results(self):
        """Test search when the query has no keywords in common."""
        query = "xyzabc" # No matching terms
        top_k = 2

        # Mock FAISS to return some results
        semantic_indices = np.array([[3, 4, 0, 1, 2]]) # Prefers docs 3 and 4
        self.rag.index.search.return_value = (None, semantic_indices)
        self.rag.embedding_model.encode.return_value = np.random.rand(1, 384).astype('float32')

        results = self.rag.search_index(query, k=top_k)

        # Should fall back to pure semantic search.
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], self.documents[3]) # "The sun shines..."
        self.assertEqual(results[1], self.documents[4]) # "A lazy cat..."

if __name__ == '__main__':
    unittest.main()
