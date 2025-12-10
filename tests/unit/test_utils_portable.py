import importlib
import io
import json
import sys
import types
from pathlib import Path

import pytest


def _stub_structlog(monkeypatch: pytest.MonkeyPatch):
    class _Logger:
        def info(self, *_, **__):
            return None

        def warning(self, *_, **__):
            return None

        def error(self, *_, **__):
            return None

        def exception(self, *_, **__):
            return None

    structlog_stub = types.SimpleNamespace(get_logger=lambda *args, **kwargs: _Logger())
    monkeypatch.setitem(sys.modules, "structlog", structlog_stub)


def _load_file_utils(monkeypatch: pytest.MonkeyPatch):
    _stub_structlog(monkeypatch)
    return importlib.reload(importlib.import_module("src.utils.file_utils"))


def _load_config_validator(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    _stub_structlog(monkeypatch)

    class DummyPaths:
        def __init__(self, values: dict[str, str]):
            self.temp_upload_dir = values.get("temp_upload_dir", "")
            self.cache_dir = values.get("cache_dir", "")
            self.logs_dir = values.get("logs_dir", "")

    class DummySettings:
        def __init__(self, **kwargs):
            paths_config = kwargs.get("paths", {})
            self.paths = DummyPaths(paths_config)

    runtime_settings = DummySettings(
        paths={
            "temp_upload_dir": str(tmp_path / "temp"),
            "cache_dir": str(tmp_path / "cache"),
            "logs_dir": str(tmp_path / "logs"),
        }
    )

    for path in [
        runtime_settings.paths.temp_upload_dir,
        runtime_settings.paths.cache_dir,
        runtime_settings.paths.logs_dir,
    ]:
        Path(path).mkdir(parents=True, exist_ok=True)

    class FakeYaml:
        @staticmethod
        def safe_load(stream):
            return json.load(stream)

    monkeypatch.setitem(sys.modules, "src.config", types.SimpleNamespace(Settings=DummySettings, get_settings=lambda: runtime_settings))
    monkeypatch.setitem(sys.modules, "yaml", FakeYaml)

    return importlib.reload(importlib.import_module("src.utils.config_validator"))


def test_chunk_text_prefers_line_boundaries():
    from src.utils.text_utils import chunk_text

    content = "Line1\nLine2\nLine3"
    chunks = chunk_text(content, max_chars=8)

    assert chunks[0] == "Line1\n"
    assert chunks[1] == "Line2\n"
    assert chunks[2] == "Line3"


def test_chunk_text_handles_short_input():
    from src.utils.text_utils import chunk_text

    assert chunk_text("short", max_chars=10) == ["short"]


def test_clear_temp_uploads_removes_items(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    file_utils = _load_file_utils(monkeypatch)
    target_dir = tmp_path / "uploads"
    nested_dir = target_dir / "nested"
    target_dir.mkdir()
    nested_dir.mkdir(parents=True)
    file_path = target_dir / "example.txt"
    file_path.write_text("data", encoding="utf-8")
    (nested_dir / "child.txt").write_text("child", encoding="utf-8")

    file_utils.clear_temp_uploads(str(target_dir))

    assert list(target_dir.iterdir()) == []


def test_clear_temp_uploads_handles_missing_and_non_directory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    file_utils = _load_file_utils(monkeypatch)
    missing_dir = tmp_path / "missing"
    non_dir = tmp_path / "file.txt"
    non_dir.write_text("content", encoding="utf-8")

    file_utils.clear_temp_uploads(str(missing_dir))
    file_utils.clear_temp_uploads(str(non_dir))

    assert non_dir.exists()


def test_safe_print_replaces_unicode(tmp_path: Path):
    from src.utils import unicode_safe

    buffer = io.StringIO()
    unicode_safe.safe_print("✅ done", "🚀 launch", file=buffer)
    assert "[OK]" in buffer.getvalue()
    assert "[LAUNCH]" in buffer.getvalue()


def test_config_validator_accepts_complete_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    config_validator = _load_config_validator(monkeypatch, tmp_path)
    config_path = tmp_path / "config.json"
    config_data = {
        "database": {"url": f"sqlite:///{tmp_path}/db.sqlite", "pool_size": 2, "max_overflow": 1},
        "auth": {"algorithm": "HS256", "access_token_expire_minutes": 60},
        "maintenance": {"purge_retention_days": 30},
        "paths": {
            "temp_upload_dir": str(tmp_path / "temp"),
            "api_url": "http://localhost", 
            "rule_dir": str(tmp_path / "rules"),
            "cache_dir": str(tmp_path / "cache"),
            "logs_dir": str(tmp_path / "logs"),
        },
        "models": {
            "retriever": "basic", 
            "fact_checker": "fc", 
            "ner_ensemble": ["n1"],
            "doc_classifier_prompt": str(tmp_path / "cls.txt"),
            "analysis_prompt_template": str(tmp_path / "analysis.txt"),
            "nlg_prompt_template": str(tmp_path / "nlg.txt"),
        },
        "llm": {"model_type": "local", "model_repo_id": "repo", "context_length": 10},
        "retrieval": {"similarity_top_k": 5, "dense_model_name": "dense", "rrf_k": 1},
        "analysis": {"confidence_threshold": 0.8},
    }
    for prompt in ["cls.txt", "analysis.txt", "nlg.txt"]:
        (tmp_path / prompt).write_text("template", encoding="utf-8")

    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    is_valid, errors, warnings = config_validator.ConfigValidator().validate_config_file(str(config_path))

    assert is_valid is True
    assert errors == []
    assert isinstance(warnings, list)


def test_config_validator_generates_health_report(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    config_validator = _load_config_validator(monkeypatch, tmp_path)
    config_path = tmp_path / "config.json"
    config_content = {
        "database": {"url": f"sqlite:///{tmp_path}/db.sqlite"},
        "auth": {"algorithm": "HS256", "access_token_expire_minutes": 30},
        "maintenance": {"purge_retention_days": 7},
        "paths": {
            "temp_upload_dir": str(tmp_path / "temp"),
            "api_url": "http://localhost", 
            "rule_dir": str(tmp_path / "rules"),
            "cache_dir": str(tmp_path / "cache"),
            "logs_dir": str(tmp_path / "logs"),
        },
        "models": {
            "retriever": "basic", 
            "fact_checker": "fc", 
            "ner_ensemble": ["n1"],
            "doc_classifier_prompt": str(tmp_path / "cls.txt"),
            "analysis_prompt_template": str(tmp_path / "analysis.txt"),
            "nlg_prompt_template": str(tmp_path / "nlg.txt"),
        },
        "llm": {"model_type": "local", "model_repo_id": "repo", "context_length": 10},
        "retrieval": {"similarity_top_k": 5, "dense_model_name": "dense", "rrf_k": 1},
        "analysis": {"confidence_threshold": 0.8},
    }
    for prompt in ["cls.txt", "analysis.txt", "nlg.txt"]:
        (tmp_path / prompt).write_text("template", encoding="utf-8")
    config_path.write_text(json.dumps(config_content), encoding="utf-8")
    default_path = tmp_path / "config.yaml"
    default_path.write_text(json.dumps(config_content), encoding="utf-8")

    monkeypatch.setenv("SECRET_KEY", "secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///memory")
    monkeypatch.chdir(tmp_path)

    validator = config_validator.ConfigValidator()
    validator.validate_config_file(str(config_path))
    report = validator.generate_health_report()

    assert report["overall_status"] in {"healthy", "warning"}
    assert report["config_validation"]["valid"] is True
    assert config_validator.validate_configuration() is True
    assert Path("config_health_report.json").exists()

