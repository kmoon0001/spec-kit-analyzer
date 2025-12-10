"""Minimal httpx compatibility stub for offline test runs.

This stub provides the small subset of the httpx API required by the
project's async test fixtures so that imports succeed when the real
httpx package cannot be installed in restricted environments.
"""

from typing import Any, Optional
import importlib


_STARLETTE_SPEC = importlib.util.find_spec("starlette")
_HAS_STARLETTE_CLIENT = bool(_STARLETTE_SPEC and importlib.util.find_spec("starlette.testclient"))


if _HAS_STARLETTE_CLIENT:
    from starlette.testclient import TestClient
else:
    class TestClient:  # type: ignore[too-many-instance-attributes]
        """Minimal placeholder when Starlette's TestClient is unavailable."""

        def __init__(self, *_, **__):
            self.headers: dict[str, str] = {}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def request(self, *_: Any, **__: Any):
            raise RuntimeError(
                "The httpx stub requires starlette.testclient for request handling. "
                "Install starlette or run tests that do not depend on ASGI routing."
            )


class Response:
    """Lightweight response wrapper mimicking the httpx interface."""

    def __init__(self, status_code: int = 200, json_data: Any | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self) -> Any:
        return self._json_data


class ASGITransport:
    """Stub transport capturing the ASGI application under test."""

    def __init__(self, app: Any | None = None, lifespan: str | None = None, **_: Any) -> None:
        self.app = app
        self.lifespan = lifespan


class AsyncClient:
    """Async-compatible client that proxies requests to the ASGI app when available."""

    def __init__(self, transport: Optional[ASGITransport] = None, base_url: str = "", **_: Any) -> None:
        self.transport = transport
        self.base_url = base_url.rstrip("/")

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        return None

    async def get(self, url: str, **kwargs: Any) -> Response:
        return await self._request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> Response:
        return await self._request("POST", url, **kwargs)

    async def _request(self, method: str, url: str, **kwargs: Any) -> Response:
        if not self.transport or not getattr(self.transport, "app", None):
            raise RuntimeError("httpx stub requires an ASGITransport with an app instance")

        with TestClient(self.transport.app, base_url=self.base_url or "http://test") as client:
            result = client.request(method, url, **kwargs)

        content_type = result.headers.get("content-type", "")
        json_payload: Any | None = None
        if content_type.startswith("application/json"):
            json_payload = result.json()

        return Response(status_code=result.status_code, json_data=json_payload, text=result.text)


__all__ = ["ASGITransport", "AsyncClient", "Response"]
