"""Function-calling security assessment engine."""

from __future__ import annotations

from app.assessment_engines.architectures._common import ArchitectureAssessmentEngine
from app.assessment_payloads.architectures.functions import LIBRARY
from app.assessment_payloads.types import PayloadLibrary


class FunctionCallingSecurityAssessmentEngine(ArchitectureAssessmentEngine):
    """Assess function schemas, allowlists, and argument safety."""

    ARCHITECTURE = "function_calling"
    CATEGORY = "agent"
    ASSESSMENT_KEY = "function-calling-security"

    @property
    def name(self) -> str:
        return "Function Calling Security Assessment"

    def payload_library(self) -> PayloadLibrary:
        return LIBRARY

    def recommendation_for(self, check: str) -> str:
        mapping = {
            "invalid_parameters": (
                "Reject function calls that fail type/schema validation."
            ),
            "unexpected_functions": (
                "Only permit declared functions from the published tool schema."
            ),
            "hallucinated_functions": (
                "Fail closed when the model invents functions that are not registered."
            ),
            "missing_required_parameters": (
                "Enforce required parameters before dispatching function calls."
            ),
            "unsafe_function_arguments": (
                "Sanitize arguments and block command/injection patterns."
            ),
        }
        return mapping.get(check, super().recommendation_for(check))
