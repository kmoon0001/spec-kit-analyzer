import os
import sys
import pytest
from unittest.mock import MagicMock

# Ensure the src directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.gui.main_window import MainApplicationWindow as MainWindow

# Some AI models can be slow to download, so we'll use a generous timeout for this test.
@pytest.mark.timeout(600)
def test_full_analysis_pipeline(qtbot):
    """
    An end-to-end test that runs the entire analysis pipeline on a test file.
    This verifies that the LLM-based analysis is working correctly.
    """
    # 1. Initialize the main window
    window = MainWindow()
    qtbot.addWidget(window)

    # 2. Wait for the LLM and Guideline services to load in the background.
    def models_loaded():
        return window.local_rag is not None and window.local_rag.is_ready() and \
               window.guideline_service is not None and window.guideline_service.is_index_ready

    qtbot.waitUntil(models_loaded, timeout=580000)

    # 3. Configure the analysis settings programmatically
    window._current_report_path = os.path.abspath("test_data/bad_note_1.txt")
    window.chk_pt.setChecked(True)
    window.chk_ot.setChecked(True)
    window.chk_slp.setChecked(True)

    # Mock the `_open_path` function to prevent it from trying to open the PDF report
    window._open_path = MagicMock()

    # 4. Trigger the analysis action
    window.action_analyze()

    # 5. Assert that the results are valid and contain our new features
    results = window.current_report_data

    assert results is not None, "Analysis did not produce any results."

    issues = results.get("issues", [])
    assert len(issues) > 0, "The LLM-based analysis failed to find any issues in the bad note."

    first_issue = issues[0]
    assert "reasoning" in first_issue, "The issue dictionary is missing the 'reasoning' field from the LLM."
    assert len(first_issue["reasoning"]) > 0, "The 'reasoning' field is empty."

    assert "confidence" in first_issue, "The issue is missing a 'confidence' score."
    assert isinstance(first_issue["confidence"], float)

    print("\n--- Verification Summary ---")
    print(f"Analysis of '{window._current_report_path}' complete.")
    print(f"Found {len(issues)} issues.")
    print(f"Reasoning for first issue ('{first_issue['title']}'): {first_issue['reasoning']}")
    print("End-to-end test passed successfully.")
    print("--------------------------")
