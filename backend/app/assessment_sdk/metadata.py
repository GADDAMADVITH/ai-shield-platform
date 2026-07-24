"""Reusable assessment metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class AssessmentMetadata:
    """Cross-cutting metadata attached to an assessment result."""

    version: str | None = None
    author: str | None = None
    execution_environment: str | None = None
    engine: str | None = None
    timestamp: datetime = field(default_factory=_utcnow)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "version": self.version,
            "author": self.author,
            "execution_environment": self.execution_environment,
            "engine": self.engine,
            "timestamp": self.timestamp.isoformat(),
        }
        if self.extra:
            payload.update(self.extra)
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> AssessmentMetadata:
        if not data:
            return cls()
        known = {
            "version",
            "author",
            "execution_environment",
            "engine",
            "timestamp",
            "extra",
        }
        raw_ts = data.get("timestamp")
        if isinstance(raw_ts, datetime):
            timestamp = raw_ts
        elif isinstance(raw_ts, str) and raw_ts:
            timestamp = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
        else:
            timestamp = _utcnow()
        extra = dict(data.get("extra") or {})
        for key, value in data.items():
            if key not in known:
                extra[key] = value
        return cls(
            version=data.get("version"),
            author=data.get("author"),
            execution_environment=data.get("execution_environment"),
            engine=data.get("engine"),
            timestamp=timestamp,
            extra=extra,
        )

    def with_extra(self, **kwargs: Any) -> AssessmentMetadata:
        return AssessmentMetadata(
            version=self.version,
            author=self.author,
            execution_environment=self.execution_environment,
            engine=self.engine,
            timestamp=self.timestamp,
            extra={**self.extra, **kwargs},
        )
