"""Assessment engine registry — maps catalog keys to engine instances."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from app.assessment_engines.base import AssessmentEngine
from app.assessment_engines.dummy import DummyAssessmentEngine
from app.common.exceptions import AppError, ConflictError, NotFoundError


class DuplicateEngineRegistrationError(ConflictError):
    """Raised when an assessment key is already registered."""

    def __init__(self, assessment_key: str) -> None:
        super().__init__(
            f"Assessment engine already registered for key {assessment_key!r}",
            details={"assessment_key": assessment_key},
        )


class EngineNotFoundError(NotFoundError):
    """Raised when no engine is registered for an assessment key."""

    def __init__(self, assessment_key: str) -> None:
        super().__init__(
            f"No assessment engine registered for key {assessment_key!r}",
            details={"assessment_key": assessment_key},
        )


class AssessmentRegistry:
    """In-memory registry of assessment engines.

    The registry knows engines only through the :class:`AssessmentEngine`
    interface — never implementation details.
    """

    def __init__(self) -> None:
        self._engines: dict[str, AssessmentEngine] = {}

    def register(self, engine: AssessmentEngine, *, replace: bool = False) -> None:
        """Register an engine under its ``assessment_key``.

        Args:
            engine: Engine instance to register.
            replace: When True, overwrite an existing registration.

        Raises:
            DuplicateEngineRegistrationError: If the key exists and replace is False.
            AppError: If the engine key is empty.
        """
        key = (engine.assessment_key or "").strip()
        if not key:
            raise AppError(
                "Assessment engine assessment_key must be a non-empty string",
                code="invalid_engine_key",
                status_code=400,
            )
        if key in self._engines and not replace:
            raise DuplicateEngineRegistrationError(key)
        self._engines[key] = engine

    def get(self, assessment_key: str) -> AssessmentEngine:
        """Return the engine registered for *assessment_key*."""
        try:
            return self._engines[assessment_key]
        except KeyError as exc:
            raise EngineNotFoundError(assessment_key) from exc

    def has(self, assessment_key: str) -> bool:
        return assessment_key in self._engines

    def unregister(self, assessment_key: str) -> None:
        self._engines.pop(assessment_key, None)

    def clear(self) -> None:
        self._engines.clear()

    def keys(self) -> list[str]:
        return sorted(self._engines)

    def items(self) -> list[tuple[str, AssessmentEngine]]:
        return sorted(self._engines.items(), key=lambda pair: pair[0])

    def as_mapping(self) -> Mapping[str, AssessmentEngine]:
        return dict(self._engines)

    def __len__(self) -> int:
        return len(self._engines)

    def __contains__(self, assessment_key: object) -> bool:
        return isinstance(assessment_key, str) and assessment_key in self._engines

    def register_many(self, engines: Iterable[AssessmentEngine], *, replace: bool = False) -> None:
        for engine in engines:
            self.register(engine, replace=replace)


def create_default_registry(*, include_dummy: bool = True) -> AssessmentRegistry:
    """Build a registry with framework-default engines.

    Sprint 7 registers only the dummy engine for orchestration validation.
    """
    registry = AssessmentRegistry()
    if include_dummy:
        registry.register(DummyAssessmentEngine())
    return registry
