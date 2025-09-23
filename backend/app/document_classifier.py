from typing import Dict, List, Tuple

def classify_document(document_text: str) -> str:
    """
    Classifies the document type based on keywords.
    The order of checks determines the priority.
    """
    document_text_lower = document_text.lower()

    # Define keywords for each document type
    # The order is important, as some notes might contain keywords from others
    # (e.g., a discharge summary might mention progress).
    classification_rules: Dict[str, List[str]] = {
        "Discharge Summary": ["discharge summary", "d/c summary", "discharge note"],
        "Evaluation / Recertification": ["evaluation", "re-evaluation", "recertification", "initial examination", "plan of care"],
        "Progress Report": ["progress note", "weekly summary", "progress report"],
        "Daily Note": ["daily note", "treatment note", "daily treatment"],
    }

    for doc_type, keywords in classification_rules.items():
        if any(keyword in document_text_lower for keyword in keywords):
            return doc_type
 
    return "Unknown Document Type"
