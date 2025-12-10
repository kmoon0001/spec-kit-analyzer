import io
import sys
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if "structlog" not in sys.modules:
    class _StructlogLogger:
        def warning(self, *_, **__):
            pass

        def error(self, *_, **__):
            pass

        def info(self, *_, **__):
            pass

        def exception(self, *_, **__):
            pass

    sys.modules["structlog"] = types.SimpleNamespace(
        get_logger=lambda *_: _StructlogLogger()
    )

from src.utils import file_utils, unicode_safe


def test_clear_temp_uploads_handles_missing_and_non_directory(monkeypatch, tmp_path):
    missing_dir = tmp_path / "does-not-exist"
    file_path = tmp_path / "not_a_dir.txt"
    file_path.write_text("content", encoding="utf-8")

    log_calls: list[tuple[str, str | None]] = []

    class _LoggerStub:
        def warning(self, message, path=None):
            log_calls.append(("warning", path))

        def error(self, message, path=None):
            log_calls.append(("error", path))

        def info(self, *_, **__):
            pass

        def exception(self, *_, **__):
            pass

    monkeypatch.setattr(file_utils, "logger", _LoggerStub())

    file_utils.clear_temp_uploads(str(missing_dir))
    file_utils.clear_temp_uploads(str(file_path))

    assert ("warning", str(missing_dir)) in log_calls
    assert ("error", str(file_path)) in log_calls
    assert file_path.exists(), "Non-directory path should not be removed"


def test_clear_temp_uploads_removes_contents(tmp_path):
    temp_dir = tmp_path / "uploads"
    nested_dir = temp_dir / "nested"
    nested_dir.mkdir(parents=True)
    (temp_dir / "file.txt").write_text("data", encoding="utf-8")
    (nested_dir / "child.txt").write_text("data", encoding="utf-8")

    file_utils.clear_temp_uploads(str(temp_dir))

    assert temp_dir.exists()
    assert list(temp_dir.iterdir()) == []


def test_safe_print_replaces_unicode_and_respects_separators():
    buffer = io.StringIO()

    unicode_safe.safe_print("✅", "done", sep="|", file=buffer)

    assert buffer.getvalue() == "[OK]|done\n"


def test_safe_print_falls_back_on_encoding_error():
    writes: list[str] = []

    class _StrictWriter:
        def write(self, text):
            # Simulate an encoding failure for non-ASCII text only on the first call
            if any(ord(ch) > 127 for ch in text):
                raise UnicodeEncodeError("ascii", text, 0, 1, "bad char")
            writes.append(text)

        def flush(self):  # pragma: no cover - flush not used but required by print
            pass

    unicode_safe.safe_print("café", file=_StrictWriter())

    assert writes and writes[0] == "caf?\n"

