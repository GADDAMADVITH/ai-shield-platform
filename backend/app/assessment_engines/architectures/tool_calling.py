"""Tool-calling security assessment engine."""

from __future__ import annotations

from app.assessment_engines.architectures._common import ArchitectureAssessmentEngine
from app.assessment_payloads.architectures.tool_calling import LIBRARY
from app.assessment_payloads.types import PayloadLibrary


class ToolCallingSecurityAssessmentEngine(ArchitectureAssessmentEngine):
    """Assess tool routing, parameter validation, and tool-output trust boundaries."""

    ARCHITECTURE = "tool_calling"
    CATEGORY = "agent"
    ASSESSMENT_KEY = "tool-calling-security"

    @property
    def name(self) -> str:
        return "Tool Calling Security Assessment"

    def payload_library(self) -> PayloadLibrary:
        return LIBRARY

    def recommendation_for(self, check: str) -> str:
        mapping = {
            "unauthorized_tool_usage": (
                "Enforce a strict tool allowlist per agent role and deny undeclared tools."
            ),
            "parameter_manipulation": (
                "Validate and sanitize tool arguments against schemas and path policies."
            ),
            "tool_invocation_validation": (
                "Require schema-validated invocations before any tool side effect."
            ),
            "unexpected_tool_selection": (
                "Score tool relevance and block unrelated high-impact tools."
            ),
            "tool_output_validation": (
                "Treat tool output as untrusted; validate before acting on it."
            ),
        }
        return mapping.get(check, super().recommendation_for(check))
