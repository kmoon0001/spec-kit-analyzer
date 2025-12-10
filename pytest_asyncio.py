"""Lightweight offline fallback for ``pytest_asyncio``.

This stub provides enough behavior to run async fixtures and tests in
environments where the real plugin cannot be installed (e.g., no internet
access). It mirrors the ``fixture`` decorator and a basic test runner hook
that executes coroutine tests on the active event loop.
"""
from __future__ import annotations

import asyncio
import inspect
from typing import Any, Callable

import pytest

FixtureFunction = Callable[..., Any]


def _get_loop_from_item(pyfuncitem: Any) -> asyncio.AbstractEventLoop:
    existing = pyfuncitem.funcargs.get("event_loop") if hasattr(pyfuncitem, "funcargs") else None
    if isinstance(existing, asyncio.AbstractEventLoop):
        return existing

    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def fixture(*args: Any, **kwargs: Any):
    """Drop-in replacement for ``pytest_asyncio.fixture``.

    Async fixtures are executed to completion on the active event loop, while
    synchronous fixtures delegate to ``pytest.fixture`` unchanged.
    """

    def decorator(func: FixtureFunction) -> FixtureFunction:
        if inspect.iscoroutinefunction(func):

            @pytest.fixture(*args, **kwargs)
            def _async_fixture_wrapper(*w_args: Any, **w_kwargs: Any):
                loop = _get_loop_from_item(type("_Dummy", (), {"funcargs": {}})())
                return loop.run_until_complete(func(*w_args, **w_kwargs))

            return _async_fixture_wrapper  # type: ignore[return-value]

        return pytest.fixture(*args, **kwargs)(func)  # type: ignore[return-value]

    return decorator


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: Any) -> bool | None:
    """Execute coroutine tests on the active event loop.

    This mimics the essential behavior of ``pytest-asyncio`` so async test
    functions are awaited instead of returning a bare coroutine object.
    """

    if inspect.iscoroutinefunction(pyfuncitem.obj):
        loop = _get_loop_from_item(pyfuncitem)
        loop.run_until_complete(pyfuncitem.obj(**pyfuncitem.funcargs))
        return True
    return None


# Expose ``mark.asyncio`` compatibility
mark = pytest.mark
