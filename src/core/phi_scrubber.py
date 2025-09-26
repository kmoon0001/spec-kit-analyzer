import re


def scrub_phi(text: str) -> str:
    if not isinstance(text, str):
        return text
    patterns = [
        (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]"),
        (r"(\+?\d{1,2}[\s\-.]?)?(\(?\d{3}\)?[ \-.]?\d{3}[\-.]?\d{4})", "[PHONE]"),
        (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
        (r"\bMRN[:\s]*[A-Za-z0-9\-]{4,}\b", "[MRN]"),
        (r"\b(19|20)\d{2}-/ (0?[1-9]|1[0-2])-/ (0?[1-g]|[12]\d|3[01])\b", "[DATE]"),
        (r"\b(Name|Patient|DOB|Address)[:\s]+[^\n]+", r"\1: [REDACTED]"),
    ]
    out = text
    for pat, repl in patterns:
        out = re.sub(pat, repl, out)
    return out
