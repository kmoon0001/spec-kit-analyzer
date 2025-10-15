"""Utilities for patching Qt thread pool behaviour during tests.

The default ``QThreadPool.waitForDone`` implementation blocks the calling
thread without processing the Qt event queue. Our GUI stability tests rely on
signal delivery while ``waitForDone`` is in progress, so we patch the method to
pump events cooperatively.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from PySide6.QtCore import QCoreApplication, QThreadPool

logger = logging.getLogger(__name__)

_ORIGINAL_WAIT_FOR_DONE = QThreadPool.waitForDone
_PATCH_APPLIED = False


def _compute_deadline(timeout_ms: int) -> Optional[float]:
    """Return an absolute ``time.monotonic`` deadline for the timeout."""

    if timeout_ms < 0:
        return None
    return time.monotonic() + timeout_ms / 1000.0


def _current_time() -> float:
    """Expose ``time.monotonic`` for easier testing."""

    return time.monotonic()


def ensure_threadpool_wait_patch() -> None:
    """Patch ``QThreadPool.waitForDone`` to keep the Qt event loop servicing."""

    global _PATCH_APPLIED
    if _PATCH_APPLIED:
        return

    def _wait_for_done(self: QThreadPool, timeout_ms: int = -1) -> bool:
        app = QCoreApplication.instance()
        if app is None:
            return _ORIGINAL_WAIT_FOR_DONE(self, timeout_ms)

        deadline = _compute_deadline(timeout_ms)
        poll_interval = 0.01  # seconds

        while True:
            completed = _ORIGINAL_WAIT_FOR_DONE(self, 0)
            app.processEvents()

            if completed:
                app.processEvents()  # Flush any signals queued during completion
                return True

            if deadline is not None and _current_time() >= deadline:
                logger.warning(
                    "QThreadPool.waitForDone timed out after %sms while %s threads active",
                    timeout_ms,
                    self.activeThreadCount(),
                )
                return False

            time.sleep(poll_interval)

    QThreadPool.waitForDone = _wait_for_done  # type: ignore[assignment]
    _PATCH_APPLIED = True
    logger.debug("Patched QThreadPool.waitForDone to process Qt events during waits")
