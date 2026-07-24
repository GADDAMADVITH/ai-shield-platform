"""Assessment engine registry — maps catalog keys to engine instances.

Implementation lives in :mod:`app.assessment_engines.registry`. This module
re-exports the public API so Sprint 7 orchestration imports keep working.
"""

from __future__ import annotations

from app.assessment_engines.registry import (
    AssessmentRegistry,
    DuplicateEngineRegistrationError,
    EngineNotFoundError,
    create_default_registry,
    discover_engine_classes,
    instantiate_discovered_engines,
)

__all__ = [
    "AssessmentRegistry",
    "DuplicateEngineRegistrationError",
    "EngineNotFoundError",
    "create_default_registry",
    "discover_engine_classes",
    "instantiate_discovered_engines",
]
