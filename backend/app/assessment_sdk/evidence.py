"""Reusable Evidence model for assessment engines."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Evidence:
    """Captured artifacts that support an assessment finding or result.

    Future-ready for screenshots and file attachments via ``attachments``.
    """

    request: dict[str, Any] | str | None = None
    response: dict[str, Any] | str | None = None
    prompt: str | None = None
    completion: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    logs: list[str | dict[str, Any]] = field(default_factory=list)
    attachments: list[dict[str, Any]] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def add_log(self, message: str, *, level: str = "info", **fields: Any) -> None:
        entry: dict[str, Any] = {"level": level, "message": message, **fields}
        self.logs.append(entry)

    def add_attachment(
        self,
        *,
        name: str,
        content_type: str,
        data: Any = None,
        uri: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a future screenshot/file artifact without requiring bytes now."""
        self.attachments.append(
            {
                "name": name,
                "content_type": content_type,
                "data": data,
                "uri": uri,
                "metadata": metadata or {},
            }
        )

    def merge(self, other: Evidence) -> Evidence:
        """Return a new Evidence combining self and *other* (other wins on scalars)."""
        return Evidence(
            request=other.request if other.request is not None else self.request,
            response=other.response if other.response is not None else self.response,
            prompt=other.prompt if other.prompt is not None else self.prompt,
            completion=other.completion if other.completion is not None else self.completion,
            headers={**self.headers, **other.headers},
            logs=[*self.logs, *other.logs],
            attachments=[*self.attachments, *other.attachments],
            extra={**self.extra, **other.extra},
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "request": self.request,
            "response": self.response,
            "prompt": self.prompt,
            "completion": self.completion,
            "headers": dict(self.headers),
            "logs": list(self.logs),
            "attachments": list(self.attachments),
        }
        # Flatten custom keys for orchestration / persistence compatibility.
        payload.update(dict(self.extra))
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Evidence:
        if not data:
            return cls()
        known = {
            "request",
            "response",
            "prompt",
            "completion",
            "headers",
            "logs",
            "attachments",
            "extra",
        }
        extra = dict(data.get("extra") or {})
        for key, value in data.items():
            if key not in known:
                extra[key] = value
        return cls(
            request=data.get("request"),
            response=data.get("response"),
            prompt=data.get("prompt"),
            completion=data.get("completion"),
            headers=dict(data.get("headers") or {}),
            logs=list(data.get("logs") or []),
            attachments=list(data.get("attachments") or []),
            extra=extra,
        )
