import re
import spacy

# Load the spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # This is a fallback for environments where the model isn't pre-installed.
    # In a production setup, the model should be part of the deployment package.
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def scrub_phi_with_ner(text: str) -> str:
    """
    Scrub PHI using a Named Entity Recognition (NER) model.
    This version correctly handles entity replacements of different lengths.
    """
    if not isinstance(text, str):
        return text

    doc = nlp(text)
    new_text_parts = []
    last_end = 0

    for ent in doc.ents:
        if ent.label_ in ["PERSON", "DATE", "GPE", "ORG"]:
            new_text_parts.append(text[last_end:ent.start_char])
            new_text_parts.append(f"[{ent.label_}]")
            last_end = ent.end_char

    new_text_parts.append(text[last_end:])

    return "".join(new_text_parts)


def scrub_phi_regex(text: str) -> str:
    """
    Scrub PHI using regular expressions for specific, structured data.
    """
    if not isinstance(text, str):
        return text
    patterns = [
        (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]"),
        (r"(\+?\d{1,2}[\s\-.]?)?(\(?\d{3}\)?[ \-.]?\d{3}[\-.]?\d{4})", "[PHONE]"),
        (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
        (r"\bMRN[:\s]*[A-Za-z0-9\-]{4,}\b", "[MRN]"),
    ]
    out = text
    for pat, repl in patterns:
        out = re.sub(pat, repl, out)
    return out


def scrub_phi(text: str) -> str:
    """
    Scrub PHI using a hybrid approach (regex first, then NER).
    """
    if not isinstance(text, str):
        return text

    # First, use regex for specific, structured patterns that NER might miss.
    regex_scrubbed_text = scrub_phi_regex(text)

    # Then, use the NER model for broad categories like names, dates, and locations.
    final_scrubbed_text = scrub_phi_with_ner(regex_scrubbed_text)

    return final_scrubbed_text