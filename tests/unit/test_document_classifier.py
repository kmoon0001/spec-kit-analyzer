import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from document_classifier import DocumentClassifier, DocumentType

def test_classify_evaluation():
    classifier = DocumentClassifier()
    text = "This is a patient evaluation and assessment."
    assert classifier.classify(text) == DocumentType.EVALUATION

def test_classify_progress_note():
    classifier = DocumentClassifier()
    text = "This is a daily progress note."
    assert classifier.classify(text) == DocumentType.PROGRESS_NOTE

def test_classify_unknown():
    classifier = DocumentClassifier()
    text = "This is a standard document with no keywords."
    assert classifier.classify(text) == DocumentType.UNKNOWN

def test_classify_case_insensitivity():
    classifier = DocumentClassifier()
    text = "this is an EVALUATION."
    assert classifier.classify(text) == DocumentType.EVALUATION
