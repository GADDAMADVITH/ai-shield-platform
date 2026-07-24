"""Shared payload types for assessment corpora."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AssessmentPayload:
    """A single reusable test prompt / probe definition."""

    id: str
    prompt: str
    category: str
    tags: tuple[str, ...] = ()
    expected_behavior: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("AssessmentPayload.id is required")
        # Frozen dataclass: use object.__setattr__ only if we needed mutation;
        # validation alone is enough here.


class PayloadLibrary:
    """Selectable collection of :class:`AssessmentPayload` entries."""

    def __init__(self, payloads: Sequence[AssessmentPayload]) -> None:
        seen: set[str] = set()
        ordered: list[AssessmentPayload] = []
        for payload in payloads:
            if payload.id in seen:
                raise ValueError(f"Duplicate payload id: {payload.id!r}")
            seen.add(payload.id)
            ordered.append(payload)
        self._payloads = tuple(ordered)
        self._by_id = {p.id: p for p in ordered}

    def all(self) -> tuple[AssessmentPayload, ...]:
        return self._payloads

    def get(self, payload_id: str) -> AssessmentPayload:
        try:
            return self._by_id[payload_id]
        except KeyError as exc:
            raise KeyError(f"Unknown payload id: {payload_id!r}") from exc

    def select(
        self,
        payload_ids: Sequence[str] | None = None,
        *,
        tags: Sequence[str] | None = None,
        categories: Sequence[str] | None = None,
    ) -> list[AssessmentPayload]:
        """Return payloads filtered by id and/or tags/categories.

        When *payload_ids* is ``None``, all payloads are candidates. Empty
        *payload_ids* yields an empty list.
        """
        if payload_ids is not None:
            selected = [self.get(pid) for pid in payload_ids]
        else:
            selected = list(self._payloads)

        if tags:
            tag_set = {t.lower() for t in tags}
            selected = [p for p in selected if tag_set.intersection(t.lower() for t in p.tags)]
        if categories:
            cat_set = {c.lower() for c in categories}
            selected = [p for p in selected if p.category.lower() in cat_set]
        return selected

    def ids(self) -> list[str]:
        return [p.id for p in self._payloads]

    def __len__(self) -> int:
        return len(self._payloads)

    def __iter__(self):
        return iter(self._payloads)

    def __contains__(self, payload_id: object) -> bool:
        return isinstance(payload_id, str) and payload_id in self._by_id
