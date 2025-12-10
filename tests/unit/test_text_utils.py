import pytest

from src.core import text_utils


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, ""),
        (123, ""),
        ("Hello\nWorld\t!", "HelloWorld!"),
        ("   spaced   out   text   ", "spaced out text"),
    ],
)
def test_sanitize_human_text_basic_and_non_string(value, expected):
    assert text_utils.sanitize_human_text(value) == expected


def test_sanitize_human_text_truncates_extremely_long_strings():
    long_chunk = "".join(str(i) for i in range(10010))
    sanitized = text_utils.sanitize_human_text(long_chunk)
    assert sanitized.endswith("... [truncated]")
    assert len(sanitized) < len(long_chunk)


def test_sanitize_human_text_detects_repetitive_patterns():
    repeated = ("abcde" * 10) * 6  # First 50 characters repeated six times
    assert (
        text_utils.sanitize_human_text(repeated)
        == "Text appears to be corrupted or repetitive. Please try again."
    )


def test_sanitize_human_text_preserves_spacing_when_not_collapsing():
    value = "signal   noise"
    sanitized = text_utils.sanitize_human_text(value, collapse_whitespace=False)
    assert sanitized == "signal   noise"


@pytest.mark.parametrize(
    "items, limit, expected",
    [
        (["A", "a", "B", "b", "C"], 10, ["A", "B", "C"]),
        (["A", " ", "", "B"], 10, ["A", "B"]),
        (["one", "two", "three", "four"], 2, ["one", "two"]),
    ],
)
def test_sanitize_bullets_deduplicates_filters_and_limits(items, limit, expected):
    assert text_utils.sanitize_bullets(items, limit=limit) == expected


def test_sanitize_bullets_applies_text_sanitization():
    items = ["first\nitem", "second\titem", "third"]
    assert text_utils.sanitize_bullets(items) == ["firstitem", "seconditem", "third"]
