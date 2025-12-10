import types

import pytest

from src.core import analysis_status_tracker
from src.core.analysis_status_tracker import AnalysisState, AnalysisStatusTracker


class _FakeTime:
    def __init__(self, start: float = 0.0):
        self.value = start

    def time(self) -> float:  # pragma: no cover - simple passthrough
        return self.value

    def advance(self, delta: float) -> None:
        self.value += delta


@pytest.fixture
def frozen_time(monkeypatch: pytest.MonkeyPatch) -> _FakeTime:
    clock = _FakeTime()
    monkeypatch.setattr(analysis_status_tracker.time, "time", clock.time)
    return clock


def test_start_tracking_sets_initial_state_and_triggers_callback(frozen_time: _FakeTime):
    tracker = AnalysisStatusTracker(timeout_threshold=5)
    callbacks: list[types.MappingProxyType[str, object] | dict[str, object]] = []
    tracker.add_status_callback(
        AnalysisState.STARTING, lambda summary: callbacks.append(summary)
    )

    tracker.start_tracking("analysis-1", "/tmp/file.pdf", "hipaa")

    assert tracker.current_analysis == "analysis-1"
    assert tracker.state is AnalysisState.STARTING
    assert tracker.progress == 0
    assert tracker.metadata["file_path"] == "/tmp/file.pdf"
    assert tracker.metadata["rubric"] == "hipaa"
    assert callbacks and callbacks[0]["state"] == AnalysisState.STARTING.value


def test_update_status_handles_timeout_and_triggers_hooks(
    frozen_time: _FakeTime,
):
    tracker = AnalysisStatusTracker(timeout_threshold=3)
    timeout_notifications: list[dict[str, object]] = []

    tracker.add_timeout_callback(timeout_notifications.append)
    tracker.add_status_callback(
        AnalysisState.TIMEOUT, lambda summary: timeout_notifications.append(summary)
    )

    tracker.start_tracking("analysis-2", "/tmp/file.pdf", "hipaa")
    frozen_time.advance(1)

    tracker.update_status(
        AnalysisState.PROCESSING, progress=15, message="Processing batch"
    )
    assert tracker.state is AnalysisState.PROCESSING
    assert tracker.progress == 15
    assert tracker.status_message == "Processing batch"

    frozen_time.advance(5)
    tracker.last_update -= tracker.timeout_threshold + 1

    assert tracker.check_timeout() is True
    tracker._handle_timeout()

    assert tracker.state is AnalysisState.TIMEOUT
    assert "timed out" in tracker.status_message
    assert timeout_notifications
    assert timeout_notifications[0]["state"] == AnalysisState.TIMEOUT.value


def test_set_error_updates_summary_and_stops_activity(frozen_time: _FakeTime):
    tracker = AnalysisStatusTracker(timeout_threshold=10)
    tracker.start_tracking("analysis-3", "/tmp/file.pdf", "hipaa")

    frozen_time.advance(2)
    tracker.set_error("database unreachable")

    summary = tracker.get_status_summary()
    assert summary["state"] == AnalysisState.FAILED.value
    assert summary["error_message"] == "database unreachable"
    assert summary["is_active"] is False
    assert summary["progress"] == tracker.progress == 0
