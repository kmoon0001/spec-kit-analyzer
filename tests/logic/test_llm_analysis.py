import pytest
from src.llm_analyzer import run_llm_analysis

def test_llm_analysis_placeholder():
    """
    Tests that the placeholder run_llm_analysis function returns an empty list.
    """
    issues = run_llm_analysis(chunks=[], rules=[], file_path="")
    assert issues == []
