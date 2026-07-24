"""Reusable Recommendation model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.assessment_sdk.severity import Severity


@dataclass(slots=True)
class Recommendation:
    """Actionable remediation guidance produced by an assessment."""

    title: str
    description: str
    priority: Severity = Severity.MEDIUM
    reference: str | None = None
    mitigation_steps: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.title = self.title.strip()
        self.description = self.description.strip()
        if not self.title:
            raise ValueError("Recommendation.title is required")
        if isinstance(self.priority, str):
            self.priority = Severity(self.priority.lower())

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "reference": self.reference,
            "mitigation_steps": list(self.mitigation_steps),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Recommendation:
        return cls(
            title=str(data["title"]),
            description=str(data.get("description") or ""),
            priority=Severity(str(data.get("priority") or Severity.MEDIUM.value).lower()),
            reference=data.get("reference"),
            mitigation_steps=list(data.get("mitigation_steps") or []),
        )
