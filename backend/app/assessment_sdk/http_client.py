"""Reusable async HTTP client for assessment engines."""

from __future__ import annotations

from types import TracebackType
from typing import Any, Self

import httpx

from app.assessment_sdk.exceptions import AssessmentTimeoutError, ConnectionError, ExecutionError


class AssessmentHttpClient:
    """Thin async HTTP helper with timeouts, auth, SSL, and session reuse."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float = 30.0,
        headers: dict[str, str] | None = None,
        api_key: str | None = None,
        verify_ssl: bool = True,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._owns_client = client is None
        default_headers = dict(headers or {})
        if api_key and "Authorization" not in default_headers:
            default_headers["Authorization"] = f"Bearer {api_key}"
        self._client = client or httpx.AsyncClient(
            base_url=base_url or "",
            timeout=httpx.Timeout(timeout_seconds),
            headers=default_headers,
            verify=verify_ssl,
        )

    @property
    def raw(self) -> httpx.AsyncClient:
        return self._client

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: Any = None,
        content: Any = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        try:
            return await self._client.request(
                method.upper(),
                url,
                headers=headers,
                params=params,
                json=json,
                content=content,
                timeout=timeout,
            )
        except httpx.TimeoutException as exc:
            raise AssessmentTimeoutError(
                f"HTTP request timed out: {method.upper()} {url}",
                details={"method": method, "url": url},
            ) from exc
        except httpx.HTTPError as exc:
            raise ConnectionError(
                f"HTTP request failed: {method.upper()} {url}",
                details={"method": method, "url": url, "error": str(exc)},
            ) from exc

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("DELETE", url, **kwargs)

    async def get_json(self, url: str, **kwargs: Any) -> Any:
        response = await self.get(url, **kwargs)
        return self._read_json(response)

    async def post_json(self, url: str, **kwargs: Any) -> Any:
        response = await self.post(url, **kwargs)
        return self._read_json(response)

    @staticmethod
    def _read_json(response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError as exc:
            raise ExecutionError(
                "Response body is not valid JSON",
                details={"status_code": response.status_code, "body": response.text[:500]},
            ) from exc

    @classmethod
    def from_existing(cls, client: httpx.AsyncClient) -> AssessmentHttpClient:
        """Wrap an existing AsyncClient (e.g. from ScanContext) without closing it."""
        return cls(client=client)
