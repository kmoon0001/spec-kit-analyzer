import json
import sys
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if "dotenv" not in sys.modules:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *_, **__: None)

if "src.config" not in sys.modules:
    dummy_paths = types.SimpleNamespace(
        temp_upload_dir=".", cache_dir=".", logs_dir="."
    )
    sys.modules["src.config"] = types.SimpleNamespace(
        Settings=lambda **kwargs: None, get_settings=lambda: types.SimpleNamespace(paths=dummy_paths)
    )

if "yaml" not in sys.modules:
    yaml = types.SimpleNamespace(
        safe_load=lambda stream: json.load(stream)
        if hasattr(stream, "read")
        else json.loads(stream),
        safe_dump=lambda data, stream: stream.write(json.dumps(data)),
        YAMLError=ValueError,
    )
    sys.modules["yaml"] = yaml
import yaml

from src.utils import config_validator


def _write_valid_config(config_path: Path) -> dict:
    temp_dir = config_path.parent / "uploads"
    rule_dir = config_path.parent / "rules"
    db_path = config_path.parent / "app.sqlite"

    config_data = {
        "database": {
            "url": f"sqlite:///{db_path}",
            "pool_size": 2,
            "max_overflow": 1,
        },
        "auth": {},
        "maintenance": {},
        "paths": {
            "temp_upload_dir": str(temp_dir),
            "api_url": "http://localhost",  # valid scheme suppresses warning
            "rule_dir": str(rule_dir),
        },
        "models": {
            "retriever": "basic",
            "fact_checker": "stub",
            "ner_ensemble": "stub",
        },
        "llm": {},
        "retrieval": {},
        "analysis": {},
        "performance": {
            "max_cache_memory_mb": 1024,
            "max_workers": 2,
            "analysis_timeout_minutes": 5,
            "model_load_timeout_minutes": 5,
            "api_request_timeout_seconds": 30,
        },
        "security": {
            "max_file_size_mb": 50,
            "allowed_file_extensions": [".txt", ".pdf"],
            "enable_rate_limiting": True,
            "max_requests_per_minute": 60,
        },
    }

    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as config_file:
        yaml.safe_dump(config_data, config_file)

    return config_data


def test_validate_config_file_missing(tmp_path):
    validator = config_validator.ConfigValidator()

    is_valid, errors, warnings = validator.validate_config_file(
        str(tmp_path / "absent.yaml")
    )

    assert not is_valid
    assert errors and "Configuration file not found" in errors[0]
    assert warnings == []


def test_validate_config_file_success(monkeypatch, tmp_path):
    config_path = tmp_path / "config.yaml"
    _write_valid_config(config_path)
    (config_path.parent / "cache").mkdir(parents=True, exist_ok=True)
    (config_path.parent / "logs").mkdir(parents=True, exist_ok=True)

    # Avoid depending on the real pydantic Settings model
    monkeypatch.setattr(config_validator, "Settings", lambda **_: object())

    validator = config_validator.ConfigValidator()
    is_valid, errors, warnings = validator.validate_config_file(str(config_path))

    assert is_valid
    assert errors == []
    assert warnings == []
    assert (config_path.parent / "uploads").exists()
    assert (config_path.parent / "rules").exists()


def test_health_report_and_validation_output(monkeypatch, tmp_path):
    config_path = tmp_path / "config.yaml"
    _write_valid_config(config_path)

    # Ensure recommended environment variables are present for a "healthy" status
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///memory")

    # Stub Settings and get_settings to use writable temporary paths
    monkeypatch.setattr(config_validator, "Settings", lambda **_: object())

    class _DummyPaths:
        def __init__(self, base: Path):
            self.temp_upload_dir = str(base / "uploads")
            self.cache_dir = str(base / "cache")
            self.logs_dir = str(base / "logs")

    class _DummySettings:
        def __init__(self, base: Path):
            self.paths = _DummyPaths(base)

    monkeypatch.setattr(
        config_validator, "get_settings", lambda: _DummySettings(config_path.parent)
    )

    # Avoid platform-specific permission reporting skewing the overall status
    monkeypatch.setattr(
        config_validator.ConfigValidator,
        "validate_file_permissions",
        lambda self: (True, []),
    )

    # Run validation from within the temporary directory so generated files stay isolated
    monkeypatch.chdir(config_path.parent)
    is_valid = config_validator.validate_configuration()

    with (config_path.parent / "config_health_report.json").open(
        encoding="utf-8"
    ) as report_file:
        report = json.load(report_file)

    assert is_valid
    assert report["overall_status"] == "healthy"
    assert report["config_validation"]["errors"] == []
    assert report["environment_check"]["missing_variables"] == []


def test_save_and_load_health_report(monkeypatch, tmp_path):
    report_path = tmp_path / "reports" / "health.json"

    class _LoggerStub:
        def __init__(self):
            self.infos = []
            self.warnings = []

        def info(self, *_args, **kwargs):
            self.infos.append(kwargs)

        def warning(self, *_args, **kwargs):  # pragma: no cover - not expected in success path
            self.warnings.append(kwargs)

    logger_stub = _LoggerStub()
    monkeypatch.setattr(config_validator, "logger", logger_stub)

    saved = config_validator.save_health_report({"status": "ok"}, str(report_path))

    assert saved is True
    assert report_path.exists()
    assert json.loads(report_path.read_text(encoding="utf-8")) == {"status": "ok"}
    assert any(
        isinstance(info.get("extra"), dict) and "path" in info["extra"]
        for info in logger_stub.infos
    )

    loaded = config_validator.ConfigValidator().load_saved_health_report(
        str(report_path)
    )

    assert loaded == {"status": "ok"}


def test_load_health_report_missing(monkeypatch, tmp_path):
    missing_path = tmp_path / "absent" / "health.json"
    calls: list[dict] = []

    class _LoggerStub:
        def info(self, *_args, **kwargs):
            calls.append(kwargs)

        def warning(self, *_args, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(config_validator, "logger", _LoggerStub())

    loaded = config_validator.ConfigValidator().load_saved_health_report(
        str(missing_path)
    )

    assert loaded == {}
    assert calls, "missing health report should log an info message"

