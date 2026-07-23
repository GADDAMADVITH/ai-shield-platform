"""Shared HTTP helpers for connectors."""

from __future__ import annotations

import time
from collections.abc import Mapping
from datetime import UTC, datetime

import httpx

from app.connectors.base import ConnectionTestResult


async def probe_http_get(
    url: str,
    *,
    timeout_seconds: int,
    verify_ssl: bool,
    headers: Mapping[str, str] | None = None,
    success_message: str = "Endpoint reachable",
) -> ConnectionTestResult:
    """Perform a timed GET probe and normalize the result."""
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(
            timeout=timeout_seconds,
            verify=verify_ssl,
            follow_redirects=True,
        ) as client:
            response = await client.get(url, headers=dict(headers or {}))
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        reachable = response.status_code < 500
        message = (
            success_message
            if reachable
            else f"Endpoint returned server error ({response.status_code})"
        )
        return ConnectionTestResult(
            reachable=reachable,
            status_code=response.status_code,
            response_time_ms=elapsed_ms,
            message=message,
            timestamp=datetime.now(UTC),
        )
    except httpx.TimeoutException:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return ConnectionTestResult.fail(
            message=f"Request timed out after {timeout_seconds}s",
            response_time_ms=elapsed_ms,
        )
    except httpx.HTTPError as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return ConnectionTestResult.fail(
            message=f"Connection failed: {exc.__class__.__name__}",
            response_time_ms=elapsed_ms,
        )
