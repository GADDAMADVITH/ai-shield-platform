"""Reusable Finding model."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from app.assessment_sdk.evidence import Evidence
from app.assessment_sdk.severity import Severity


@dataclass(slots=True)
class Finding:
    """A single security finding discovered during an assessment."""

    title: str
    description: str
    severity: Severity = Severity.MEDIUM
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: str | None = None
    confidence: float | None = None
    affected_component: str | None = None
    recommendation: str | None = None
    evidence: Evidence = field(default_factory=Evidence)
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.title = self.title.strip()
        self.description = self.description.strip()
        if not self.title:
            raise ValueError("Finding.title is required")
        if isinstance(self.severity, str):
            self.severity = Severity(self.severity.lower())
        if self.confidence is not None and not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("Finding.confidence must be between 0.0 and 1.0")
        if isinstance(self.evidence, dict):
            self.evidence = Evidence.from_dict(self.evidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "category": self.category,
            "confidence": self.confidence,
            "affected_component": self.affected_component,
            "recommendation": self.recommendation,
            "evidence": self.evidence.to_dict(),
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Finding:
        return cls(
            id=str(data.get("id") or uuid.uuid4()),
            title=str(data["title"]),
            description=str(data.get("description") or ""),
            severity=Severity(str(data.get("severity") or Severity.MEDIUM.value).lower()),
            category=data.get("category"),
            confidence=data.get("confidence"),
            affected_component=data.get("affected_component"),
            recommendation=data.get("recommendation"),
            evidence=Evidence.from_dict(
                data.get("evidence") if isinstance(data.get("evidence"), dict) else {}
            ),
            tags=list(data.get("tags") or []),
        )
