import os
import logging
from src.core.analysis_service import AnalysisService

# Configure logging to see the output from the services
logging.basicConfig(level=logging.INFO)
logging.getLogger("transformers").setLevel(logging.WARNING) # Suppress verbose transformer logs

def test_pipeline():
    """
    Tests the full RAG pipeline from AnalysisService.
    """
    print("--- Starting RAG Pipeline Test ---")

    # 1. Initialize the AnalysisService
    # This will also initialize the GuidelineService and the LLMComplianceAnalyzer,
    # and download the necessary models. This might take a while on the first run.
    print("Initializing AnalysisService...")
    try:
        analysis_service = AnalysisService()
        print("AnalysisService initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize AnalysisService: {e}")
        return

    # 2. Define the path to a test document
    test_file = os.path.join("test_data", "good_note_1.txt")
    if not os.path.exists(test_file):
        print(f"Error: Test file not found at {test_file}")
        return

    print(f"\nAnalyzing test file: {test_file}")

    # 3. Run the analysis
    try:
        report_html = analysis_service.analyze_document(test_file)
        print("\n--- Analysis Complete ---")
        print("Generated HTML Report:")
        print("="*80)
        print(report_html)
        print("="*80)
    except Exception as e:
        print(f"\nAn error occurred during analysis: {e}")

    print("\n--- RAG Pipeline Test Finished ---")


if __name__ == "__main__":
    test_pipeline()
