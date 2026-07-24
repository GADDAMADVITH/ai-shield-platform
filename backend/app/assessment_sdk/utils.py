"""Small shared helpers for assessment engines."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any


def truncate(text: str | None, *, max_chars: int = 2_000) -> str:
    """Truncate text for safe evidence/logging storage."""
    if text is None:
        return ""
    value = str(text)
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 3] + "..."


def safe_get(mapping: dict[str, Any] | None, *keys: str, default: Any = None) -> Any:
    """Nested dict getter: ``safe_get(data, 'a', 'b')`` → ``data['a']['b']``."""
    current: Any = mapping or {}
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


@asynccontextmanager
async def timed_section() -> AsyncIterator[Callable[[], float]]:
    """Async context manager yielding a callable that returns elapsed ms."""
    started = time.perf_counter()

    def elapsed_ms() -> float:
        return (time.perf_counter() - started) * 1000

    yield elapsed_ms


async def maybe_await[T](value: T | Awaitable[T]) -> T:
    """Await *value* when it is awaitable; otherwise return it directly."""
    if isinstance(value, Awaitable):
        return await value  # type: ignore[misc]
    return value
