import importlib
import json
import sys
import types
from pathlib import Path

import pytest


def _load_validator(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
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

    monkeypatch.setitem(
        sys.modules,
        "src.config",
        types.SimpleNamespace(Settings=DummySettings, get_settings=lambda: runtime_settings),
    )
    monkeypatch.setitem(sys.modules, "yaml", FakeYaml)

    return importlib.reload(importlib.import_module("src.utils.config_validator"))


def test_validate_structure_missing_sections(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    config_validator = _load_validator(monkeypatch, tmp_path)
    validator = config_validator.ConfigValidator()

    validator._validate_structure({})

    for section in [
        "database",
        "auth",
        "maintenance",
        "paths",
        "models",
        "llm",
        "retrieval",
        "analysis",
    ]:
        assert any(section in err for err in validator.validation_errors)


def test_validate_models_generator_profiles(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    config_validator = _load_validator(monkeypatch, tmp_path)
    validator = config_validator.ConfigValidator()

    validator._validate_models(
        {
            "generator_profiles": {"quick": {"repo": "id-only"}},
        }
    )

    assert any("Missing required model configuration" in err for err in validator.validation_errors)
    assert any("generator profile" in err.lower() for err in validator.validation_errors)


def test_validate_performance_thresholds(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    config_validator = _load_validator(monkeypatch, tmp_path)
    validator = config_validator.ConfigValidator()

    validator._validate_performance(
        {
            "max_cache_memory_mb": 128,
            "max_workers": 0,
            "analysis_timeout_minutes": 0,
        }
    )

    assert any("very low" in warning for warning in validator.validation_warnings)
    assert any("max_workers must be at least 1" == err for err in validator.validation_errors)
    assert any("must be positive" in err for err in validator.validation_errors)


def test_validate_security_rules(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    config_validator = _load_validator(monkeypatch, tmp_path)
    validator = config_validator.ConfigValidator()

    validator._validate_security(
        {
            "max_file_size_mb": 0,
            "allowed_file_extensions": ["txt", ".pdf"],
            "enable_rate_limiting": True,
            "max_requests_per_minute": 5,
        }
    )

    assert any("very low" in warning for warning in validator.validation_warnings)
    assert any("dot" in warning for warning in validator.validation_warnings)
    assert any("very low" in warning for warning in validator.validation_warnings)


def test_validate_paths_warns_for_api_and_files(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    config_validator = _load_validator(monkeypatch, tmp_path)
    validator = config_validator.ConfigValidator()

    existing_dir = tmp_path / "rules"
    existing_dir.mkdir(parents=True, exist_ok=True)

    temp_dir = tmp_path / "temp"
    validator._validate_paths(
        {
            "api_url": "localhost",  # missing scheme should warn
            "temp_upload_dir": str(temp_dir),
            "rule_dir": str(existing_dir),
        }
    )

    assert any("http" in warning for warning in validator.validation_warnings)
    assert temp_dir.exists()
    assert existing_dir.exists()


def test_check_environment_variables_reports_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    config_validator = _load_validator(monkeypatch, tmp_path)
    validator = config_validator.ConfigValidator()

    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    valid, missing = validator.check_environment_variables()

    assert valid is False
    assert all(entry.startswith("Recommended environment variable") for entry in missing)
