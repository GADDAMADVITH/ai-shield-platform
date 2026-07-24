"""Assessment engine registry with automatic discovery.

Canonical registry for engines lives here. The orchestration package re-exports
these types for backward compatibility with Sprint 7/7.1 call sites.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from collections.abc import Iterable, Mapping, Sequence

from app.assessment_engines.base import AssessmentEngine
from app.assessment_engines.dummy import DummyAssessmentEngine
from app.common.exceptions import AppError, ConflictError, NotFoundError

UNIVERSAL_PACKAGE = "app.assessment_engines.universal"


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
        """Register an engine under its ``assessment_key``."""
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


def discover_engine_classes(
    package_name: str = UNIVERSAL_PACKAGE,
) -> list[type[AssessmentEngine]]:
    """Import *package_name* submodules and collect concrete engine classes.

    Modules whose names start with ``_`` are skipped. Abstract bases and the
    ``AssessmentEngine`` ABC itself are ignored.
    """
    package = importlib.import_module(package_name)
    paths: Sequence[str] = list(getattr(package, "__path__", []))
    discovered: dict[str, type[AssessmentEngine]] = {}

    for module_info in pkgutil.iter_modules(paths):
        if module_info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{package_name}.{module_info.name}")
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if obj is AssessmentEngine:
                continue
            if not issubclass(obj, AssessmentEngine):
                continue
            if inspect.isabstract(obj):
                continue
            # Only engines defined in this module (avoid re-exports).
            if obj.__module__ != module.__name__:
                continue
            discovered[obj.__name__] = obj

    return sorted(discovered.values(), key=lambda cls: cls.__name__)


def instantiate_discovered_engines(
    package_name: str = UNIVERSAL_PACKAGE,
) -> list[AssessmentEngine]:
    """Discover and instantiate engines from *package_name*."""
    return [cls() for cls in discover_engine_classes(package_name)]


def create_default_registry(
    *,
    include_dummy: bool = True,
    include_universal: bool = True,
    discover: bool = True,
) -> AssessmentRegistry:
    """Build a registry with framework-default engines.

    When *discover* is True (default), universal engines are loaded via
    automatic package discovery. When False, falls back to the explicit
    ``UNIVERSAL_ENGINES`` export list.
    """
    registry = AssessmentRegistry()
    if include_dummy:
        registry.register(DummyAssessmentEngine())
    if include_universal:
        if discover:
            engines = instantiate_discovered_engines()
        else:
            from app.assessment_engines.universal import UNIVERSAL_ENGINES

            engines = [cls() for cls in UNIVERSAL_ENGINES]
        registry.register_many(engines)
    return registry
