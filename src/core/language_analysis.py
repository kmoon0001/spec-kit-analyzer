"""
Patient-Centered Language Analysis Module

This module provides functionality to analyze clinical documentation for its
use of patient-centered language. It calculates a score based on a predefined
set of patient-centered and passive/impersonal phrases.
"""

import re
from typing import Dict, List, Tuple

# Pre-compiled regex for sentence splitting for efficiency
SENTENCE_SPLITTER = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s')

# --- Keyword Dictionaries ---
# These lists define the phrases we're looking for. They are case-insensitive.

PATIENT_CENTERED_PHRASES: List[str] = [
    "patient states",
    "client reports",
    "patient expresses",
    "patient's goal is",
    "patient's goals are",
    "we discussed",
    "collaborated on",
    "patient and i",
    "client and i",
    "patient participated in",
    "patient's progress",
    "patient-reported outcome",
    "patient-specific",
    "agreed upon",
    "patient's preference",
    "family reports"
]

PASSIVE_IMPERSONAL_PHRASES: List[str] = [
    "it was noted",
    "it was observed",
    "was seen for",
    "therapy was provided",
    "treatment was administered",
    "subjective complaints include",
    "the patient was instructed",
    "patient tolerated well",
    "patient was encouraged",
    "is a poor historian",
    "patient denies",
    "uncooperative with"
]

def analyze_patient_centered_language(text: str) -> Dict:
    """
    Analyzes a block of text for patient-centered language and returns a score
    and detailed findings.

    Args:
        text: The clinical documentation text to analyze.

    Returns:
        A dictionary containing the score, the number of patient-centered and
        passive phrases found, and the specific phrases identified.
    """
    if not text or not isinstance(text, str):
        return {
            "score": 0,
            "patient_centered_count": 0,
            "passive_count": 0,
            "patient_centered_phrases_found": [],
            "passive_phrases_found": []
        }

    lower_text = text.lower()

    # Find all occurrences of the phrases
    patient_centered_found: List[str] = [phrase for phrase in PATIENT_CENTERED_PHRASES if phrase in lower_text]
    passive_found: List[str] = [phrase for phrase in PASSIVE_IMPERSONAL_PHRASES if phrase in lower_text]

    patient_centered_count = len(patient_centered_found)
    passive_count = len(passive_found)
    total_phrases = patient_centered_count + passive_count

    # Calculate score
    if total_phrases == 0:
        # If no relevant phrases are found, we can't score. Return a neutral/default state.
        score = 50  # A neutral score, indicating neither good nor bad, just not applicable.
    else:
        # Score is the percentage of phrases that are patient-centered.
        score = int((patient_centered_count / total_phrases) * 100)

    return {
        "score": score,
        "patient_centered_count": patient_centered_count,
        "passive_count": passive_count,
        "patient_centered_phrases_found": list(set(patient_centered_found)), # Return unique phrases
        "passive_phrases_found": list(set(passive_found))
    }

# Example usage:
if __name__ == '__main__':
    example_note_good = """
    Session Start. Patient states he is "feeling much stronger this week".
    We discussed his progress toward his goal of walking his dog.
    Patient's goal is to be able to walk for 20 minutes without stopping.
    Collaborated on a new exercise to improve balance. Patient participated in all activities.
    """

    example_note_bad = """
    Patient was seen for therapy. It was noted that there were subjective complaints of pain.
    Therapy was provided for 30 minutes. Patient was instructed on home exercises.
    Patient tolerated well.
    """

    good_analysis = analyze_patient_centered_language(example_note_good)
    print("--- Good Example Analysis ---")
    print(f"Score: {good_analysis['score']}%")
    print(f"Patient-Centered Phrases: {good_analysis['patient_centered_phrases_found']}")
    print(f"Passive Phrases: {good_analysis['passive_phrases_found']}")
    # Expected score: 100%

    print("\n" + "="*30 + "\n")

    bad_analysis = analyze_patient_centered_language(example_note_bad)
    print("--- Bad Example Analysis ---")
    print(f"Score: {bad_analysis['score']}%")
    print(f"Patient-Centered Phrases: {bad_analysis['patient_centered_phrases_found']}")
    print(f"Passive Phrases: {bad_analysis['passive_phrases_found']}")
    # Expected score: 0%