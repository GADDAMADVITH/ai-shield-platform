"""RAG architecture security assessment engine."""

from __future__ import annotations

from app.assessment_engines.architectures._common import ArchitectureAssessmentEngine
from app.assessment_payloads.architectures.rag import LIBRARY
from app.assessment_payloads.types import PayloadLibrary


class RagSecurityAssessmentEngine(ArchitectureAssessmentEngine):
    """Assess RAG pipelines for injection, poisoning, leakage, and grounding."""

    ARCHITECTURE = "rag"
    CATEGORY = "rag"
    ASSESSMENT_KEY = "rag-security"

    @property
    def name(self) -> str:
        return "RAG Security Assessment"

    def payload_library(self) -> PayloadLibrary:
        return LIBRARY

    def recommendation_for(self, check: str) -> str:
        mapping = {
            "prompt_injection_through_retrieved_context": (
                "Treat retrieved context as untrusted data, not instructions. "
                "Isolate system policy from document text."
            ),
            "context_poisoning": (
                "Validate and quarantine knowledge-base documents; use integrity "
                "checks and provenance controls against poisoned content."
            ),
            "retrieved_context_leakage": (
                "Never echo raw retrieved chunks; apply redaction and ACL filters "
                "before generation."
            ),
            "source_attribution_validation": (
                "Require grounded citations that map to retrieved documents; "
                "reject fabricated source labels."
            ),
            "missing_citation_detection": (
                "Enforce citation requirements for high-risk answers and refuse "
                "when grounding is unavailable."
            ),
            "chunk_manipulation": (
                "Preserve retrieval ordering/integrity and detect adversarial "
                "rewrites of retrieved chunks."
            ),
            "knowledge_boundary_violations": (
                "Constrain answers to the approved knowledge boundary and refuse "
                "out-of-corpus speculation for sensitive topics."
            ),
        }
        return mapping.get(check, super().recommendation_for(check))
