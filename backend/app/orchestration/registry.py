"""Assessment engine registry — maps catalog keys to engine instances.

Implementation lives in :mod:`app.assessment_engines.registry`. This module
re-exports the public API so Sprint 7 orchestration imports keep working.
"""

from __future__ import annotations

from app.assessment_engines.registry import (
    ARCHITECTURE_PACKAGE,
    DISCOVERY_PACKAGES,
    AssessmentRegistry,
    DuplicateEngineRegistrationError,
    EngineNotFoundError,
    create_default_registry,
    discover_all_engine_classes,
    discover_engine_classes,
    instantiate_all_discovered_engines,
    instantiate_discovered_engines,
)

__all__ = [
    "ARCHITECTURE_PACKAGE",
    "AssessmentRegistry",
    "DISCOVERY_PACKAGES",
    "DuplicateEngineRegistrationError",
    "EngineNotFoundError",
    "create_default_registry",
    "discover_all_engine_classes",
    "discover_engine_classes",
    "instantiate_all_discovered_engines",
    "instantiate_discovered_engines",
]
