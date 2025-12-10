import asyncio
import importlib
import json
import sys
import types
import uuid
from pathlib import Path

import pytest


def _stub_structlog(monkeypatch: pytest.MonkeyPatch):
    class DummyContext:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    class DummyLogger:
        def __init__(self):
            self.records: list[tuple[str, tuple, dict]] = []

        def info(self, *args, **kwargs):
            self.records.append(("info", args, kwargs))

        def warning(self, *args, **kwargs):
            self.records.append(("warning", args, kwargs))

        def exception(self, *args, **kwargs):
            self.records.append(("exception", args, kwargs))

        def error(self, *args, **kwargs):
            self.records.append(("error", args, kwargs))

    configure_calls: list[dict] = []
    dummy_logger = DummyLogger()

    structlog_stub = types.SimpleNamespace(
        contextvars=types.SimpleNamespace(
            bound_contextvars=lambda **kwargs: DummyContext(**kwargs),
            merge_contextvars=lambda **kwargs: DummyContext(**kwargs),
        ),
        stdlib=types.SimpleNamespace(
            add_logger_name=lambda *args, **kwargs: (args, kwargs),
            add_log_level=lambda *args, **kwargs: (args, kwargs),
            PositionalArgumentsFormatter=lambda: "positional",
            LoggerFactory=lambda: "factory",
            BoundLogger=object,
        ),
        processors=types.SimpleNamespace(
            TimeStamper=lambda fmt="iso": ("timestamp", fmt),
            StackInfoRenderer=lambda: "stack_info",
            format_exc_info=lambda *args, **kwargs: (args, kwargs),
            UnicodeDecoder=lambda *args, **kwargs: (args, kwargs),
            JSONRenderer=lambda *args, **kwargs: (args, kwargs),
        ),
        configure=lambda **kwargs: configure_calls.append(kwargs),
        get_logger=lambda *args, **kwargs: dummy_logger,
    )

    monkeypatch.setitem(sys.modules, "structlog", structlog_stub)
    return structlog_stub, dummy_logger, configure_calls


def _load_logging_config(monkeypatch: pytest.MonkeyPatch):
    _stub_structlog(monkeypatch)
    return importlib.reload(importlib.import_module("src.logging_config"))


def test_configure_logging_invokes_structlog(monkeypatch: pytest.MonkeyPatch):
    structlog_stub, dummy_logger, configure_calls = _stub_structlog(monkeypatch)
    module = importlib.reload(importlib.import_module("src.logging_config"))

    root_logger = importlib.import_module("logging").getLogger()
    original_level = root_logger.level
    original_handlers = list(root_logger.handlers)

    try:
        module.configure_logging(level=25)
    finally:
        for handler in list(root_logger.handlers):
            if handler not in original_handlers:
                root_logger.removeHandler(handler)
        root_logger.setLevel(original_level)

    assert configure_calls, "structlog.configure should be called"
    assert dummy_logger.records[0][0] == "info"
    assert root_logger.level == original_level


def test_correlation_id_middleware_adds_header(monkeypatch: pytest.MonkeyPatch):
    module = _load_logging_config(monkeypatch)
    monkeypatch.setattr(uuid, "uuid4", lambda: uuid.UUID(int=1))

    messages = []

    async def send(message):
        messages.append(message)

    async def app(scope, receive, send):
        await send({"type": "http.response.start", "headers": []})
        await send({"type": "http.response.body", "body": b""})

    middleware = module.CorrelationIdMiddleware(app)

    asyncio.run(middleware({"type": "http"}, lambda: {}, send))

    start_message = messages[0]
    assert start_message["type"] == "http.response.start"
    header_names = [name for name, _ in start_message["headers"]]
    assert b"X-Correlation-ID" in header_names


def test_prompt_manager_loads_and_formats(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    _, dummy_logger, _ = _stub_structlog(monkeypatch)
    module = importlib.reload(importlib.import_module("src.utils.prompt_manager"))

    template_dir = tmp_path / "resources" / "prompts"
    template_dir.mkdir(parents=True)
    template_path = template_dir / "hello.txt"
    template_path.write_text("Hello {name}!", encoding="utf-8")

    monkeypatch.setattr(module, "os", importlib.import_module("os"))
    monkeypatch.setattr(module, "__file__", str(template_dir / ".." / "placeholder"))

    prompt_manager = module.PromptManager("hello.txt")
    assert prompt_manager.get_prompt(name="Tester") == "Hello Tester!"
    assert not dummy_logger.records


def test_prompt_manager_raises_on_missing(monkeypatch: pytest.MonkeyPatch):
    _stub_structlog(monkeypatch)
    module = importlib.reload(importlib.import_module("src.utils.prompt_manager"))

    with pytest.raises(FileNotFoundError):
        module.PromptManager("missing.txt")


def test_prompt_manager_logs_missing_variable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    _, dummy_logger, _ = _stub_structlog(monkeypatch)
    module = importlib.reload(importlib.import_module("src.utils.prompt_manager"))

    template_dir = tmp_path / "resources" / "prompts"
    template_dir.mkdir(parents=True)
    template_path = template_dir / "hello.txt"
    template_path.write_text("Hello {name}!", encoding="utf-8")

    monkeypatch.setattr(module, "os", importlib.import_module("os"))
    monkeypatch.setattr(module, "__file__", str(template_dir / ".." / "placeholder"))

    prompt_manager = module.PromptManager("hello.txt")

    with pytest.raises(KeyError):
        prompt_manager.get_prompt()

    assert dummy_logger.records and dummy_logger.records[0][0] == "exception"


def test_config_validator_handles_missing_file(tmp_path: Path):
    class FakeYaml:
        @staticmethod
        def safe_load(stream):
            return json.load(stream)

    class FakeDotenv:
        @staticmethod
        def load_dotenv(*args, **kwargs):
            return None

    class FakeBaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class FakeSecretStr(str):
        pass

    sys.modules["yaml"] = FakeYaml
    sys.modules["dotenv"] = FakeDotenv
    sys.modules["src.config"] = types.SimpleNamespace(
        Settings=FakeBaseModel,
        get_settings=lambda: types.SimpleNamespace(
            paths=types.SimpleNamespace(
                temp_upload_dir="/tmp/temp_upload",
                cache_dir="/tmp/cache",
                logs_dir="/tmp/logs",
            )
        ),
    )
    sys.modules["pydantic"] = types.SimpleNamespace(
        BaseModel=FakeBaseModel, SecretStr=FakeSecretStr
    )
    sys.modules["pydantic_settings"] = types.SimpleNamespace(
        BaseSettings=FakeBaseModel, SettingsConfigDict=dict
    )
    config_validator = importlib.reload(
        importlib.import_module("src.utils.config_validator")
    )

    missing = tmp_path / "absent.yaml"
    is_valid, errors, warnings = config_validator.ConfigValidator().validate_config_file(
        str(missing)
    )

    assert is_valid is False
    assert errors and "not found" in errors[0]
    assert warnings == []


def test_config_validator_reports_permission_issues(monkeypatch: pytest.MonkeyPatch):
    class FakeYaml:
        @staticmethod
        def safe_load(stream):
            return json.load(stream)

    class FakeDotenv:
        @staticmethod
        def load_dotenv(*args, **kwargs):
            return None

    class FakeBaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class FakeSecretStr(str):
        pass

    sys.modules["yaml"] = FakeYaml
    sys.modules["dotenv"] = FakeDotenv
    sys.modules["src.config"] = types.SimpleNamespace(
        Settings=FakeBaseModel,
        get_settings=lambda: types.SimpleNamespace(
            paths=types.SimpleNamespace(
                temp_upload_dir="/tmp/temp_upload",
                cache_dir="/tmp/cache",
                logs_dir="/tmp/logs",
            )
        ),
    )
    sys.modules["pydantic"] = types.SimpleNamespace(
        BaseModel=FakeBaseModel, SecretStr=FakeSecretStr
    )
    sys.modules["pydantic_settings"] = types.SimpleNamespace(
        BaseSettings=FakeBaseModel, SettingsConfigDict=dict
    )
    config_validator = importlib.reload(
        importlib.import_module("src.utils.config_validator")
    )

    class DummyPaths:
        temp_upload_dir = "/tmp/temp_upload"
        cache_dir = "/tmp/cache"
        logs_dir = "/tmp/logs"

    monkeypatch.setattr(config_validator, "get_settings", lambda: types.SimpleNamespace(paths=DummyPaths()))
    monkeypatch.setattr(config_validator.os, "access", lambda *_, **__: False)

    valid, errors = config_validator.ConfigValidator().validate_file_permissions()

    assert valid is False
    assert len(errors) == 3


def test_config_validator_env_variable_check(monkeypatch: pytest.MonkeyPatch):
    class FakeYaml:
        @staticmethod
        def safe_load(stream):
            return json.load(stream)

    class FakeDotenv:
        @staticmethod
        def load_dotenv(*args, **kwargs):
            return None

    class FakeBaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class FakeSecretStr(str):
        pass

    sys.modules["yaml"] = FakeYaml
    sys.modules["dotenv"] = FakeDotenv
    sys.modules["src.config"] = types.SimpleNamespace(
        Settings=FakeBaseModel,
        get_settings=lambda: types.SimpleNamespace(
            paths=types.SimpleNamespace(
                temp_upload_dir="/tmp/temp_upload",
                cache_dir="/tmp/cache",
                logs_dir="/tmp/logs",
            )
        ),
    )
    sys.modules["pydantic"] = types.SimpleNamespace(
        BaseModel=FakeBaseModel, SecretStr=FakeSecretStr
    )
    sys.modules["pydantic_settings"] = types.SimpleNamespace(
        BaseSettings=FakeBaseModel, SettingsConfigDict=dict
    )
    config_validator = importlib.reload(
        importlib.import_module("src.utils.config_validator")
    )

    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    valid, missing = config_validator.ConfigValidator().check_environment_variables()

    assert valid is False
    assert all("not set" in entry for entry in missing)
