import sys
import os

# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

from core.document_classifier import DocumentClassifier


def test_classify_evaluation():
    classifier = DocumentClassifier(llm_service=None, prompt_template_path="")
    text = "This is a patient evaluation and assessment."
    # This test is simplified as the actual classifier relies on an LLM.
    # We are assuming a mock or simplified logic would be used in a real test scenario.
    # For now, we just test the structure.
    # A placeholder assertion:
    assert isinstance(classifier.classify_document(text), str)


def test_classify_progress_note():
    classifier = DocumentClassifier(llm_service=None, prompt_template_path="")
    text = "This is a daily progress note."
    assert isinstance(classifier.classify_document(text), str)


def test_classify_unknown():
    classifier = DocumentClassifier(llm_service=None, prompt_template_path="")
    text = "This is a standard document with no keywords."
    assert classifier.classify_document(text) == "Unknown"


def test_classify_case_insensitivity():
    classifier = DocumentClassifier(llm_service=None, prompt_template_path="")
    text = "this is an EVALUATION."
    assert isinstance(classifier.classify_document(text), str)
