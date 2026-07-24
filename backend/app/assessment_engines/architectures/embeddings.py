"""Embedding / vector database security assessment engine."""

from __future__ import annotations

from app.assessment_engines.architectures._common import ArchitectureAssessmentEngine
from app.assessment_payloads.architectures.embeddings import LIBRARY
from app.assessment_payloads.types import PayloadLibrary


class EmbeddingSecurityAssessmentEngine(ArchitectureAssessmentEngine):
    """Assess embedding integrity, metadata exposure, and retrieval isolation."""

    ARCHITECTURE = "embeddings"
    CATEGORY = "rag"
    ASSESSMENT_KEY = "embedding-security"

    @property
    def name(self) -> str:
        return "Embedding Security Assessment"

    def payload_library(self) -> PayloadLibrary:
        return LIBRARY

    def recommendation_for(self, check: str) -> str:
        mapping = {
            "embedding_integrity": (
                "Protect vector writes with authn/authz and integrity verification."
            ),
            "vector_metadata_exposure": (
                "Minimize metadata returned from vector queries; strip sensitive fields."
            ),
            "sensitive_context_exposure": (
                "Detect and filter sensitive content before indexing or retrieval."
            ),
            "index_leakage": (
                "Isolate indexes per tenant and deny cross-tenant catalog enumeration."
            ),
            "improper_retrieval": (
                "Enforce retrieval ACLs so callers only receive authorized documents."
            ),
        }
        return mapping.get(check, super().recommendation_for(check))
