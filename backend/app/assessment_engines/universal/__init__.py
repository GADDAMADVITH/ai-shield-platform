"""Universal security assessment engines (Sprint 9)."""

from app.assessment_engines.universal.hallucination import HallucinationAssessmentEngine
from app.assessment_engines.universal.input_validation import InputValidationAssessmentEngine
from app.assessment_engines.universal.jailbreak import JailbreakAssessmentEngine
from app.assessment_engines.universal.output_validation import OutputValidationAssessmentEngine
from app.assessment_engines.universal.prompt_injection import PromptInjectionAssessmentEngine
from app.assessment_engines.universal.prompt_leakage import PromptLeakageAssessmentEngine
from app.assessment_engines.universal.sensitive_data import SensitiveDataAssessmentEngine

UNIVERSAL_ENGINES: tuple[type, ...] = (
    PromptInjectionAssessmentEngine,
    JailbreakAssessmentEngine,
    PromptLeakageAssessmentEngine,
    HallucinationAssessmentEngine,
    SensitiveDataAssessmentEngine,
    InputValidationAssessmentEngine,
    OutputValidationAssessmentEngine,
)

__all__ = [
    "HallucinationAssessmentEngine",
    "InputValidationAssessmentEngine",
    "JailbreakAssessmentEngine",
    "OutputValidationAssessmentEngine",
    "PromptInjectionAssessmentEngine",
    "PromptLeakageAssessmentEngine",
    "SensitiveDataAssessmentEngine",
    "UNIVERSAL_ENGINES",
]
