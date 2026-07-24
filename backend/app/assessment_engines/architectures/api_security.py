"""API security assessment engine for AI-facing HTTP surfaces."""

from __future__ import annotations

from app.assessment_engines.architectures._common import ArchitectureAssessmentEngine
from app.assessment_payloads.architectures.api import LIBRARY
from app.assessment_payloads.types import PayloadLibrary


class ApiSecurityAssessmentEngine(ArchitectureAssessmentEngine):
    """Assess authentication, authorization, rate limits, validation, and leakage."""

    ARCHITECTURE = "api"
    CATEGORY = "api"
    ASSESSMENT_KEY = "api-security"

    @property
    def name(self) -> str:
        return "API Security Assessment"

    def payload_library(self) -> PayloadLibrary:
        return LIBRARY

    def recommendation_for(self, check: str) -> str:
        mapping = {
            "authentication_presence": (
                "Require authentication on protected AI endpoints; reject anonymous access."
            ),
            "authorization_checks": (
                "Enforce object-level and tenant authorization on every sensitive read/write."
            ),
            "rate_limiting": (
                "Apply request/token rate limits and return 429 under abuse conditions."
            ),
            "input_validation": (
                "Validate request size, shape, and content before model or tool invocation."
            ),
            "sensitive_data_exposure": (
                "Redact secrets and PII from API responses and logs."
            ),
            "error_information_leakage": (
                "Return generic client errors; keep stack traces server-side only."
            ),
        }
        return mapping.get(check, super().recommendation_for(check))
