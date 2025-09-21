### John Snow Labs Integration Summary

This environment has been configured to support and demonstrate the integration of a John Snow Labs (JSL) "tiny" model for Named Entity Recognition (NER).

**Key Changes:**

1.  **New JSL NER Service:** A new service, `JSLNERService`, has been created in `src/jsl_ner_service.py`. This service encapsulates the logic for running a JSL healthcare NER model.

2.  **Application Integration:** The main application logic in `src/main.py` has been modified to use this new service. The application can now use either the original BioBERT NER model or the new JSL model, controlled by a setting.

3.  **Demonstration Script:** A new script, `demo.py`, has been added to the root directory. This script provides a simple way to run the analysis pipeline and see the output of the JSL model. **It also contains detailed instructions on how to install the licensed JSL library, which is a required manual step.**

4.  **Code Cleanup:** The old, unused NER service files (`src/ner_service.py` and `src/llm_analyzer.py`) have been deleted to simplify the codebase.

**How to Use:**

1.  **Install Dependencies:**
    *   First, follow the instructions at the top of the `demo.py` file to install the licensed `spark-nlp-jsl` library using your secret key.
    *   Then, run `pip install -r requirements.txt` to install the remaining public dependencies.

2.  **Run the Demonstration:**
    *   Execute the demonstration script by running `python demo.py`. This will run the analysis on a sample file using the new JSL NER service and print the results.

3.  **Switching NER Models:**
    *   The application is currently configured to use the JSL model by default when running the demo. To switch back to the original BioBERT model, you can modify the `use_jsl_ner` setting in the application's settings database or change the default value in the `get_bool_setting("use_jsl_ner", True)` call within `src/main.py`.