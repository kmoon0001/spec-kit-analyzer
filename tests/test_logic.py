import os
import sys
import pytest
from types import SimpleNamespace

# Ensure the src directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import run_analyzer
from src.local_llm import LocalRAG
from src.guideline_service import GuidelineService
from src.rubric_service import RubricService
from src.llm_analyzer import run_llm_analysis

@pytest.mark.timeout(600)
def test_analyzer_logic_e2e():
    """
    Tests the core analysis logic end-to-end without loading the GUI.
    """
    # 1. Create a mock main window object. It just needs to hold the services.
    mock_window = SimpleNamespace()
    def log_print(x):
        print(x)
    mock_window.log = log_print

    # 2. Initialize the RAG and Guideline services, which happens in the background in the real app.
    # NOTE: This will download AI models on the first run and may take a few minutes.
    print("Loading AI models...")
    mock_window.local_rag = LocalRAG(model_repo_id="QuantFactory/Phi-3-mini-4k-instruct-GGUF", model_filename="Phi-3-mini-4k-instruct.Q2_K.gguf")
    assert mock_window.local_rag.is_ready()

    print("Loading and indexing guidelines...")
    mock_window.guideline_service = GuidelineService(mock_window.local_rag)
    mock_window.guideline_service.load_and_index_guidelines(["test_data/static_guidelines.txt"])
    assert mock_window.guideline_service.is_index_ready
    print("Models and guidelines loaded.")

    # 3. Define the parameters for the analysis run.
    test_file = os.path.abspath("test_data/bad_note_1.txt")
    disciplines = ['pt', 'ot', 'slp']

    # 4. Run the analyzer function directly.
    print(f"Starting analysis on {test_file}...")
    results = run_analyzer(
        file_path=test_file,
        selected_disciplines=disciplines,
        main_window_instance=mock_window
    )
    print("Analysis complete.")

    # 5. Assert that the results are valid and contain our new features.
    assert results is not None, "Analysis did not produce any results."

    issues = results.get("issues", [])
    assert len(issues) > 0, "The LLM-based analysis failed to find any issues in the bad note."

    first_issue = issues[0]
    assert "reasoning" in first_issue, "The issue dictionary is missing the 'reasoning' field from the LLM."
    assert len(first_issue["reasoning"]) > 0, "The 'reasoning' field is empty."

    assert "confidence" in first_issue, "The issue is missing a 'confidence' score."
    assert isinstance(first_issue["confidence"], float)

    print("\n--- Verification Summary ---")
    print(f"Found {len(issues)} issues.")
    print(f"Reasoning for first issue ('{first_issue['title']}'): {first_issue['reasoning']}")
    print("End-to-end logic test passed successfully.")
    print("--------------------------")
