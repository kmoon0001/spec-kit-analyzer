import os
import sys
import pytest
from types import SimpleNamespace

# Ensure the src directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.local_llm import LocalRAG
from src.rubric_service import RubricService
from src.llm_analyzer import run_llm_analysis
from src.text_chunking import RecursiveCharacterTextSplitter

@pytest.mark.timeout(600)
def test_llm_analysis_on_bad_note():
    """
    Tests the run_llm_analysis function directly on a known bad note.
    """
    # 1. Initialize the LLM
    print("Loading AI model...")
    local_rag = LocalRAG(model_repo_id="QuantFactory/Phi-3-mini-4k-instruct-GGUF", model_filename="Phi-3-mini-4k-instruct.Q2_K.gguf")
    assert local_rag.is_ready()
    llm = local_rag.llm
    print("AI model loaded.")

    # 2. Load the compliance rules
    print("Loading compliance rubrics...")
    disciplines = ['pt', 'ot', 'slp']
    rubric_map = {
        "pt": os.path.join(os.path.dirname(__file__), '..', 'src', "pt_compliance_rubric.ttl"),
        "ot": os.path.join(os.path.dirname(__file__), '..', 'src', "ot_compliance_rubric.ttl"),
        "slp": os.path.join(os.path.dirname(__file__), '..', 'src', "slp_compliance_rubric.ttl"),
    }
    all_rules = []
    for discipline in disciplines:
        path = rubric_map.get(discipline)
        if path and os.path.exists(path):
            service = RubricService(path)
            all_rules.extend(service.get_rules())

    seen_titles = set()
    unique_rules = []
    for rule in all_rules:
        if rule.issue_title not in seen_titles:
            unique_rules.append(rule)
            seen_titles.add(rule.issue_title)
    rules_as_dicts = [r.__dict__ for r in unique_rules]
    print(f"Loaded {len(rules_as_dicts)} unique rules.")

    # 3. Load and chunk the test data
    test_file = os.path.abspath("test_data/bad_note_1.txt")
    with open(test_file, 'r') as f:
        text = f.read()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    print(f"Split note into {len(chunks)} chunks.")

    # 4. Run the LLM analysis directly
    print("Running LLM analysis...")
    issues = run_llm_analysis(
        llm=llm,
        chunks=chunks,
        rules=rules_as_dicts,
        file_path=test_file
    )
    print(f"LLM analysis found {len(issues)} issues.")
    print("Issues found:", issues)

    # 5. Assert that issues were found
    assert len(issues) > 0, "The LLM-based analysis failed to find any issues in the bad note."
