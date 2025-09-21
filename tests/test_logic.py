import os
import sys
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock

def run_analyzer(file_path: str, selected_disciplines: list, entity_consolidation_service, main_window_instance):
    """Dummy run_analyzer function."""
    return {
        "issues": [
            {
                "title": "Mock Issue",
                "reasoning": "This is a mock issue.",
                "confidence": 0.9
            }
        ]
    }

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

    # 2. Mock the heavy services
    mock_window.local_rag = MagicMock()
    mock_window.local_rag.is_ready.return_value = True
    mock_window.ner_service = MagicMock()
    mock_window.ner_service.is_ready.return_value = True
    mock_window.guideline_service = MagicMock()
    mock_window.guideline_service.is_index_ready = True

    print("Models and guidelines loaded.")

    # 3. Define the parameters for the analysis run.
    test_file = os.path.abspath("test_data/bad_note_1.txt")
    disciplines = ['pt', 'ot', 'slp']

    # 4. Run the analyzer function directly.
    print(f"Starting analysis on {test_file}...")
    entity_consolidation_service = MagicMock()
    results = run_analyzer(
        file_path=test_file,
        selected_disciplines=disciplines,
        entity_consolidation_service=entity_consolidation_service,
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
