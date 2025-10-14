"""Minimal pytest-asyncio replacement for offline test environments."""
from __future__ import annotations

import asyncio
import atexit
import inspect
from collections.abc import Awaitable, Callable, Generator
from functools import wraps
from typing import Any, TypeVar, overload

import pytest

_T = TypeVar("_T")

# Create a single event loop shared across the entire test session. The real
# pytest-asyncio plugin offers more advanced loop management but this
# lightweight implementation focuses on providing the minimal functionality
# required by the project's asynchronous tests while avoiding external
# dependencies.
_EVENT_LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(_EVENT_LOOP)


def _run(coro: Awaitable[Any]) -> Any:
    """Execute ``coro`` on the shared event loop and return its result."""
    asyncio.set_event_loop(_EVENT_LOOP)
    return _EVENT_LOOP.run_until_complete(coro)


def _shutdown_event_loop() -> None:
    """Cleanly close the shared event loop at interpreter shutdown."""
    if _EVENT_LOOP.is_closed():
        return
    try:
        _EVENT_LOOP.run_until_complete(_EVENT_LOOP.shutdown_asyncgens())
    finally:
        _EVENT_LOOP.close()


atexit.register(_shutdown_event_loop)


@overload
def fixture(func: Callable[..., _T]) -> Callable[..., _T]:
    ...


@overload
def fixture(*args: Any, **kwargs: Any) -> Callable[[Callable[..., _T]], Callable[..., _T]]:
    ...


def fixture(*args: Any, **kwargs: Any):
    """Drop-in replacement for :func:`pytest_asyncio.fixture`.

    The decorator mirrors ``pytest.fixture`` but transparently runs coroutine
    and async generator based fixtures on the shared event loop.
    """

    if args and callable(args[0]) and not kwargs:
        return fixture()(args[0])

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.isasyncgenfunction(func):
            @pytest.fixture(*args, **kwargs)
            @wraps(func)
            def wrapper(*f_args: Any, **f_kwargs: Any) -> Generator[Any, None, None]:
                agen = func(*f_args, **f_kwargs)
                first = _run(agen.__anext__())
                try:
                    yield first
                finally:
                    try:
                        _run(agen.aclose())
                    except RuntimeError:
                        # The event loop may already be closed if the session is
                        # tearing down; ignore the error to mirror pytest's
                        # behaviour in this scenario.
                        pass

            return wrapper

        if inspect.iscoroutinefunction(func):
            @pytest.fixture(*args, **kwargs)
            @wraps(func)
            def wrapper(*f_args: Any, **f_kwargs: Any) -> Any:
                return _run(func(*f_args, **f_kwargs))

            return wrapper

        return pytest.fixture(*args, **kwargs)(func)

    return decorator


class _AsyncioPlugin:
    """Pytest plugin implementing coroutine test execution."""

    @pytest.hookimpl(tryfirst=True)
    def pytest_pyfunc_call(self, pyfuncitem: Any) -> bool | None:
        test_function = pyfuncitem.obj
        if not inspect.iscoroutinefunction(test_function):
            return None

        kwargs = pyfuncitem.funcargs
        _run(test_function(**kwargs))
        return True


_PLUGIN = _AsyncioPlugin()


def pytest_addoption(parser: pytest.Parser) -> None:  # pragma: no cover - pytest hook
    """Register the ``asyncio_mode`` ini option so pytest accepts it."""

    parser.addini(
        "asyncio_mode",
        "Control how the in-repo pytest-asyncio stub manages the event loop.",
        default="auto",
    )


def pytest_configure(config: pytest.Config) -> None:  # pragma: no cover - pytest hook
    if not config.pluginmanager.has_plugin("asyncio_stub"):
        config.pluginmanager.register(_PLUGIN, name="asyncio_stub")

    config.addinivalue_line(
        "markers",
        "asyncio: mark test to run with the shared asyncio event loop provided by the stub plugin.",
    )


__all__ = ["fixture"]
