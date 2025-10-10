"""Utility helpers for sanitising text prior to displaying it to users."""

import string
from collections.abc import Iterable

_ALLOWED_CHARS = set(string.printable) - {"", ""}


def sanitize_human_text(value: str, *, collapse_whitespace: bool = True) -> str:
    """Return a version of *value* that only contains human readable ASCII characters."""
    if not isinstance(value, str):
        return ""
    filtered = "".join(ch for ch in value if ch in _ALLOWED_CHARS)
    if collapse_whitespace:
        filtered = " ".join(filtered.split())
    return filtered.strip()


def sanitize_bullets(items: Iterable[str], *, limit: int = 6) -> list[str]:
    """Sanitise and de-duplicate bullet strings while preserving order."""
    seen = set()
    bullets: list[str] = []
    for raw in items:
        clean = sanitize_human_text(raw)
        if not clean:
            continue
        if clean.lower() in seen:
            continue
        bullets.append(clean)
        seen.add(clean.lower())
        if len(bullets) >= limit:
            break
    return bullets
