"""Pluggable assessment engines for the scan orchestration framework.

Engines return :class:`~app.assessment_sdk.result.AssessmentResult`.
"""

from app.assessment_engines.base import AssessmentEngine, EngineResult, to_engine_result
from app.assessment_engines.dummy import DummyAssessmentEngine
from app.assessment_engines.registry import (
    AssessmentRegistry,
    DuplicateEngineRegistrationError,
    EngineNotFoundError,
    create_default_registry,
    discover_engine_classes,
    instantiate_discovered_engines,
)
from app.assessment_engines.universal import (
    UNIVERSAL_ENGINES,
    HallucinationAssessmentEngine,
    InputValidationAssessmentEngine,
    JailbreakAssessmentEngine,
    OutputValidationAssessmentEngine,
    PromptInjectionAssessmentEngine,
    PromptLeakageAssessmentEngine,
    SensitiveDataAssessmentEngine,
)

__all__ = [
    "AssessmentEngine",
    "AssessmentRegistry",
    "DummyAssessmentEngine",
    "DuplicateEngineRegistrationError",
    "EngineNotFoundError",
    "EngineResult",
    "HallucinationAssessmentEngine",
    "InputValidationAssessmentEngine",
    "JailbreakAssessmentEngine",
    "OutputValidationAssessmentEngine",
    "PromptInjectionAssessmentEngine",
    "PromptLeakageAssessmentEngine",
    "SensitiveDataAssessmentEngine",
    "UNIVERSAL_ENGINES",
    "create_default_registry",
    "discover_engine_classes",
    "instantiate_discovered_engines",
    "to_engine_result",
]
