"""PyPI compatibility shim for the in-repo pytest-asyncio stub."""

from . import pytest_addoption as _pytest_addoption
from . import pytest_configure as _pytest_configure


def pytest_addoption(parser):  # pragma: no cover - thin wrapper
    """Delegate to the stub implementation residing in ``pytest_asyncio.__init__``."""

    return _pytest_addoption(parser)


def pytest_configure(config):  # pragma: no cover - thin wrapper
    """Delegate to the stub implementation residing in ``pytest_asyncio.__init__``."""

    return _pytest_configure(config)
