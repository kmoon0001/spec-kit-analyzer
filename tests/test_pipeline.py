import os
import shutil
import pytest
from src.ingestion import build_sentence_window_index
from src.retrieval import get_query_engine
from llama_index.core.llms import MockLLM
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

TEST_DOCS_DIR = "tests/test_data"
TEST_INDEX_DIR = "tests/test_index"

@pytest.fixture(scope="module")
def setup_teardown():
    """Fixture to handle setup and teardown of test files."""
    # Setup: ensure the test index directory is clean
    if os.path.exists(TEST_INDEX_DIR):
        shutil.rmtree(TEST_INDEX_DIR)

    # Create a mock LLM that returns a predictable response
    llm = MockLLM(max_tokens=256)
    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Run the ingestion pipeline
    build_sentence_window_index(
        documents_path=TEST_DOCS_DIR,
        llm=llm,
        embed_model=embed_model,
        save_dir=TEST_INDEX_DIR,
    )

    yield # This is where the testing happens

    # Teardown: clean up the created index directory
    if os.path.exists(TEST_INDEX_DIR):
        shutil.rmtree(TEST_INDEX_DIR)

def test_full_pipeline(setup_teardown):
    """
    Tests the full ingestion and query pipeline end-to-end.
    """
    # 1. Check if the index was created
    assert os.path.exists(TEST_INDEX_DIR)

    # 2. Get the query engine, passing the mock LLM
    mock_llm = MockLLM(max_tokens=256)
    query_engine = get_query_engine(index_dir=TEST_INDEX_DIR, llm=mock_llm)

    # 3. Query the engine
    question = "What is the capital of France?"
    response = query_engine.query(question)

    # 4. Assert the response is valid
    assert response is not None
    assert hasattr(response, 'response')

    # The MockLLM will typically return a response based on the context.
    # A simple assertion is to check that it's not empty.
    # A more advanced test could check the source nodes.
    assert len(response.response) > 0

    print(f"\nQuestion: {question}")
    print(f"Response: {response.response}")

    # Test another query and inspect the source nodes
    question_2 = "What is data science?"
    response_2 = query_engine.query(question_2)
    assert response_2 is not None
    assert hasattr(response_2, 'source_nodes')
    assert len(response_2.source_nodes) > 0

    # The most relevant source node should contain the definition of data science.
    top_source_content = response_2.source_nodes[0].get_content().lower()
    assert "interdisciplinary field" in top_source_content

    print(f"\nQuestion: {question_2}")
    print(f"Top source node content: {top_source_content}")
