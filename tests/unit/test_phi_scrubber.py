import types

from src.core import phi_scrubber


class _DummyOperatorConfig:
    def __init__(self, action: str, params: dict | None = None):
        self.action = action
        self.params = params or {}


def test_scrub_returns_original_when_presidio_unavailable(monkeypatch):
    monkeypatch.setattr(phi_scrubber, "AnalyzerEngine", None)
    monkeypatch.setattr(phi_scrubber, "AnonymizerEngine", None)
    monkeypatch.setattr(phi_scrubber, "OperatorConfig", None)

    service = phi_scrubber.PhiScrubberService()
    assert service.scrub("Sensitive text") == "Sensitive text"


def test_scrub_uses_custom_wrapper(monkeypatch):
    monkeypatch.setattr(phi_scrubber, "OperatorConfig", _DummyOperatorConfig)

    class Wrapper:
        def __init__(self):
            self.analyze_called = False
            self.anonymize_called = False

        def analyze(self, text):
            self.analyze_called = True
            return [types.SimpleNamespace(text=text)]

        def anonymize(self, text, analyzer_results=None, operators=None):  # pragma: no cover - integration path
            self.anonymize_called = True
            replacement = operators["DEFAULT"].params.get("new_value")
            return types.SimpleNamespace(text=f"{replacement}:{analyzer_results[0].text}")

    wrapper = Wrapper()
    service = phi_scrubber.PhiScrubberService(wrapper=wrapper)

    result = service.scrub("Sensitive text", replacement_token="<REDACTED>")

    assert result == "<REDACTED>:Sensitive text"
    assert wrapper.analyze_called is True
    assert wrapper.anonymize_called is True


def test_scrub_handles_analyzer_failure_and_returns_original(monkeypatch):
    monkeypatch.setattr(phi_scrubber, "OperatorConfig", _DummyOperatorConfig)

    class FailingAnalyzer:
        def analyze(self, text, language="en"):
            raise RuntimeError("boom")

    class DummyAnonymizer:
        def anonymize(self, text, analyzer_results=None, operators=None):  # pragma: no cover - not reached on error path
            return types.SimpleNamespace(text="should not happen")

    service = phi_scrubber.PhiScrubberService(
        analyzer=FailingAnalyzer(), anonymizer=DummyAnonymizer()
    )

    assert service.scrub("Sensitive text") == "Sensitive text"
