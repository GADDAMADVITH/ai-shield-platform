"""Architecture-specific security assessment engines (Sprint 11)."""

from app.assessment_engines.architectures.agents import AgentSecurityAssessmentEngine
from app.assessment_engines.architectures.api_security import ApiSecurityAssessmentEngine
from app.assessment_engines.architectures.embeddings import EmbeddingSecurityAssessmentEngine
from app.assessment_engines.architectures.function_calling import (
    FunctionCallingSecurityAssessmentEngine,
)
from app.assessment_engines.architectures.rag import RagSecurityAssessmentEngine
from app.assessment_engines.architectures.tool_calling import (
    ToolCallingSecurityAssessmentEngine,
)

ARCHITECTURE_ENGINES: tuple[type, ...] = (
    RagSecurityAssessmentEngine,
    AgentSecurityAssessmentEngine,
    ToolCallingSecurityAssessmentEngine,
    FunctionCallingSecurityAssessmentEngine,
    ApiSecurityAssessmentEngine,
    EmbeddingSecurityAssessmentEngine,
)

__all__ = [
    "ARCHITECTURE_ENGINES",
    "AgentSecurityAssessmentEngine",
    "ApiSecurityAssessmentEngine",
    "EmbeddingSecurityAssessmentEngine",
    "FunctionCallingSecurityAssessmentEngine",
    "RagSecurityAssessmentEngine",
    "ToolCallingSecurityAssessmentEngine",
]
