import os
import json
from pprint import pprint

# --- John Snow Labs Installation Instructions ---
#
# To run this demonstration, you need to have a valid John Snow Labs for Healthcare
# license. The 'spark-nlp-jsl' library is not public and must be installed
# with your license secret.
#
# 1. Find your license secret:
#    - Log in to your account at https://my.johnsnowlabs.com
#    - Go to the "My Subscriptions" page.
#    - Find your Healthcare NLP license and click "Show Secret" to get your license key.
#      It will look something like `5.4.0-xxxxxxxx-xxxxxxxx-xxxxxxxx-xxxxxxxx`.
#
# 2. Install the library:
#    - Open your terminal or command prompt.
#    - Run the following command, replacing `${YOUR_SECRET_CODE}` with your actual secret:
#
#      pip install spark-nlp-jsl==5.4.0 --extra-index-url https://pypi.johnsnowlabs.com/${YOUR_SECRET_CODE} --upgrade
#
# 3. Set environment variables:
#    - The JSL library uses AWS credentials to download models. Your license JSON
#      file contains an `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`.
#    - You must set these as environment variables before running the script.
#
#      For Linux/macOS:
#      export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY"
#      export AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY"
#
#      For Windows (Command Prompt):
#      set AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY"
#      set AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY"
#
# --- End of Instructions ---


try:
    from src.main import run_analyzer, EntityConsolidationService, NEREntity
    from src.jsl_ner_service import JSLNERService
    jsl_installed = True
except ImportError:
    jsl_installed = False


class DummyMainWindow:
    """A mock MainWindow class to satisfy the dependencies of run_analyzer."""
    def __init__(self):
        self.local_rag = None
        self.guideline_service = None
        self.entity_consolidation_service = EntityConsolidationService()
        self.compliance_rules = []

    def log(self, message: str):
        """A dummy logging function."""
        print(f"[App Log] {message}")

def run_demonstration():
    """
    Runs a demonstration of the analysis pipeline with the JSL NER service.
    """
    if not jsl_installed:
        print("="*80)
        print("ERROR: John Snow Labs for Healthcare is not installed.")
        print("Please follow the installation instructions at the top of this script.")
        print("="*80)
        return

    print("--- Starting John Snow Labs NER Demonstration ---")

    # Set this to True to run the demo.
    # In a real scenario, this would come from the settings UI.
    use_jsl = True

    # 1. Set up the required services and a dummy main window
    dummy_window = DummyMainWindow()
    entity_service = dummy_window.entity_consolidation_service

    # 2. Define the path to the test file
    test_file = os.path.join("test_data", "good_note_1.txt")
    if not os.path.exists(test_file):
        print(f"Error: Test file not found at {test_file}")
        return

    print(f"\nAnalyzing test file: {test_file}")

    # 3. Define the disciplines to analyze for
    selected_disciplines = ['pt', 'ot', 'slp']

    # 4. Temporarily set the 'use_jsl_ner' setting to True for this run
    from src.main import set_bool_setting
    original_setting = set_bool_setting("use_jsl_ner", True)

    print("\nRunning analyzer with JSL NER enabled...")
    results = run_analyzer(
        file_path=test_file,
        selected_disciplines=selected_disciplines,
        entity_consolidation_service=entity_service,
        main_window_instance=dummy_window
    )

    # Restore the original setting
    set_bool_setting("use_jsl_ner", original_setting)

    # 5. Process and display the results
    if results and results.get("json"):
        print("\nAnalysis complete. Loading results from JSON report...")
        with open(results["json"], "r", encoding="utf-8") as f:
            report_data = json.load(f)

        print("\n--- Extracted Entities (from JSL Model) ---")
        ner_entities_dict = report_data.get("ner_results", {})

        all_entities = []
        for model_name, entities in ner_entities_dict.items():
            print(f"\nEntities from model: '{model_name}'")
            if entities:
                for entity in entities:
                    all_entities.append(entity)
                    print(f"  - Text:    '{entity.get('text')}'")
                    print(f"    Label:   {entity.get('label')}")
                    print(f"    Score:   {entity.get('score', 0.0):.4f}")
            else:
                print("  No entities were extracted by this model.")

        if not all_entities:
            print("\nNo entities were extracted in this run.")

    else:
        print("\nAnalysis did not produce a valid result. Please check the logs.")

    print("\n--- Demonstration Complete ---")


if __name__ == "__main__":
    run_demonstration()
