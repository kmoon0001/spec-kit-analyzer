import pytest
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from core.hybrid_retriever import HybridRetriever
from src.rubric_service import ComplianceRule

@pytest.fixture(scope="module")
def retriever():
    """
    Fixture to initialize the HybridRetriever once for the entire module.
    This is useful because initializing the retriever (loading models) can be slow.
    """
    return HybridRetriever()

def test_retriever_initialization(retriever):
    """
    Tests if the HybridRetriever initializes without errors and loads rules.
    """
    assert retriever is not None
    assert retriever.rules is not None
    assert len(retriever.rules) > 0
    assert retriever.corpus is not None
    assert len(retriever.corpus) > 0
    assert retriever.bm25 is not None
    assert retriever.dense_retriever is not None
    assert retriever.corpus_embeddings is not None

def test_graph_rag_retrieval_specific_query(retriever):
    """
    Tests the GraphRAG retriever with a specific query that should match a known rule.
    """
    # This query is designed to be a close match to the "Goals" rule in the rubric.
    query = "patient goals must be measurable and time-bound"

    # Perform the search with filters that should include the "Goals" rule.
    results = retriever.search(query, discipline="pt", doc_type="Progress Note")

    # 1. Assert that we got some results back.
    assert results is not None, "Search should return a list, not None."
    assert len(results) > 0, "Search should find at least one relevant rule."

    # 2. Assert that the top result is a ComplianceRule object.
    top_result = results[0]
    assert isinstance(top_result, ComplianceRule)

    # 3. Assert that the top result is the one we expect.
    # We expect the "Goals" rule to be the most relevant.
    assert "Goals may not be measurable/time-bound" in top_result.issue_title, f"Top result should be about 'Goals may not be measurable/time-bound', but got '{top_result.issue_title}'."
    print(f"\nSuccessfully retrieved rule: '{top_result.issue_title}' for query: '{query}'")

def test_graph_rag_retrieval_another_query(retriever):
    """
    Tests the GraphRAG retriever with a different query.
    """
    # This query is designed to find the rule about missing signatures.
    query = "document is missing a signature or date"

    # Search without doc_type filter
    results = retriever.search(query, discipline="pt")

    assert results is not None
    assert len(results) > 0

    # Assert that the "Signature" rule is one of the top results.
    assert any("signature" in r.issue_title.lower() for r in results), \
        f"The 'Signature' rule was not found in the top results for query '{query}'."
    print(f"\nSuccessfully retrieved rule containing 'Signature' for query: '{query}'")

def test_graph_rag_retrieval_no_results(retriever):
    """
    Tests that the retriever returns an empty list when no rules match the filter.
    """
    query = "this should not match anything"

    # Use a filter that has no rules
    results = retriever.search(query, discipline="non_existent_discipline")

    assert results is not None
    assert isinstance(results, list)
    assert len(results) == 0
    print("\nSuccessfully handled a query with no matching rules.")
