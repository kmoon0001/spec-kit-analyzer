from types import SimpleNamespace

import pytest

from src.core.phi_scrubber import PhiScrubberService


class DummyWrapper:
    """Simple wrapper used to simulate Presidio behaviour in tests."""

    def __init__(self, phrases_to_mask):
        self.phrases_to_mask = phrases_to_mask
        self.analyze_calls = []
        self.anonymize_calls = []

    def analyze(self, text: str):
        self.analyze_calls.append(text)
        results = []
        for phrase in self.phrases_to_mask:
            start = text.find(phrase)
            if start != -1:
                results.append(SimpleNamespace(start=start, end=start + len(phrase)))
        return results

    def anonymize(self, text: str, analyzer_results, operators):
        self.anonymize_calls.append((text, analyzer_results, operators))
        replacement = operators["DEFAULT"].params.get("new_value", "<MASK>")
        for result in sorted(analyzer_results, key=lambda r: r.start, reverse=True):
            text = text[: result.start] + replacement + text[result.end :]
        return SimpleNamespace(text=text)


def test_scrub_replaces_configured_token():
    wrapper = DummyWrapper(["John Doe", "555-123-4567"])
    service = PhiScrubberService(replacement="[REDACTED]", wrapper=wrapper)

    text = "Patient John Doe can be reached at 555-123-4567."
    scrubbed = service.scrub(text)

    assert "John Doe" not in scrubbed
    assert "555-123-4567" not in scrubbed
    assert scrubbed.count("[REDACTED]") == 2


@pytest.mark.parametrize("value", [None, 1234, ["a", "b"], "   "])
def test_scrub_is_noop_for_non_text(value):
    service = PhiScrubberService(wrapper=DummyWrapper([]))
    assert service.scrub(value) is value


def test_scrub_logs_and_returns_original_when_wrapper_errors(mocker):
    faulty_wrapper = DummyWrapper(["John Doe"])
    mocker.patch.object(
        faulty_wrapper,
        "analyze",
        side_effect=RuntimeError("presidio unavailable"),
    )
    service = PhiScrubberService(wrapper=faulty_wrapper)
    assert service.scrub("Patient John Doe") == "Patient John Doe"
