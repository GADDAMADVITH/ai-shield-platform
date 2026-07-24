"""Pluggable assessment engines for the scan orchestration framework.

Engines return :class:`~app.assessment_sdk.result.AssessmentResult`.
"""

from app.assessment_engines.architectures import (
    ARCHITECTURE_ENGINES,
    AgentSecurityAssessmentEngine,
    ApiSecurityAssessmentEngine,
    EmbeddingSecurityAssessmentEngine,
    FunctionCallingSecurityAssessmentEngine,
    RagSecurityAssessmentEngine,
    ToolCallingSecurityAssessmentEngine,
)
from app.assessment_engines.base import AssessmentEngine, EngineResult, to_engine_result
from app.assessment_engines.dummy import DummyAssessmentEngine
from app.assessment_engines.registry import (
    ARCHITECTURE_PACKAGE,
    DISCOVERY_PACKAGES,
    UNIVERSAL_PACKAGE,
    AssessmentRegistry,
    DuplicateEngineRegistrationError,
    EngineNotFoundError,
    create_default_registry,
    discover_all_engine_classes,
    discover_engine_classes,
    instantiate_all_discovered_engines,
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
    "ARCHITECTURE_ENGINES",
    "ARCHITECTURE_PACKAGE",
    "AgentSecurityAssessmentEngine",
    "ApiSecurityAssessmentEngine",
    "AssessmentEngine",
    "AssessmentRegistry",
    "DISCOVERY_PACKAGES",
    "DummyAssessmentEngine",
    "DuplicateEngineRegistrationError",
    "EmbeddingSecurityAssessmentEngine",
    "EngineNotFoundError",
    "EngineResult",
    "FunctionCallingSecurityAssessmentEngine",
    "HallucinationAssessmentEngine",
    "InputValidationAssessmentEngine",
    "JailbreakAssessmentEngine",
    "OutputValidationAssessmentEngine",
    "PromptInjectionAssessmentEngine",
    "PromptLeakageAssessmentEngine",
    "RagSecurityAssessmentEngine",
    "SensitiveDataAssessmentEngine",
    "ToolCallingSecurityAssessmentEngine",
    "UNIVERSAL_ENGINES",
    "UNIVERSAL_PACKAGE",
    "create_default_registry",
    "discover_all_engine_classes",
    "discover_engine_classes",
    "instantiate_all_discovered_engines",
    "instantiate_discovered_engines",
    "to_engine_result",
]
