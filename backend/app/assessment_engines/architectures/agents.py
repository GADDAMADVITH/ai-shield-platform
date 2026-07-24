"""Agent architecture security assessment engine."""

from __future__ import annotations

from app.assessment_engines.architectures._common import ArchitectureAssessmentEngine
from app.assessment_payloads.architectures.agents import LIBRARY
from app.assessment_payloads.types import PayloadLibrary


class AgentSecurityAssessmentEngine(ArchitectureAssessmentEngine):
    """Assess autonomous agents for goal hijack, planning abuse, and unsafe actions."""

    ARCHITECTURE = "agent"
    CATEGORY = "agent"
    ASSESSMENT_KEY = "agent-security"

    @property
    def name(self) -> str:
        return "Agent Security Assessment"

    def payload_library(self) -> PayloadLibrary:
        return LIBRARY

    def recommendation_for(self, check: str) -> str:
        mapping = {
            "goal_manipulation": (
                "Pin immutable mission goals server-side and reject goal-rewrite attempts."
            ),
            "recursive_task_generation": (
                "Cap recursive task fan-out depth and total spawned tasks per run."
            ),
            "infinite_planning": (
                "Enforce planning step budgets and terminate non-converging plans."
            ),
            "unauthorized_action_requests": (
                "Require human approval for destructive/high-impact actions."
            ),
            "privilege_escalation": (
                "Run agents with least privilege; deny self-escalation of roles or scopes."
            ),
            "memory_abuse": (
                "Sanitize persistent memory writes and isolate memory by tenant/session."
            ),
            "unsafe_agent_decisions": (
                "Add policy guards and secondary validation for high-risk decisions."
            ),
        }
        return mapping.get(check, super().recommendation_for(check))
