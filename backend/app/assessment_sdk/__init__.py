"""Assessment SDK — reusable building blocks for all assessment engines.

Sprint 8 ships infrastructure only. Real security assessments land later and
must consume these models/utilities instead of inventing parallel types.
"""

from app.assessment_sdk.configuration import AssessmentConfiguration
from app.assessment_sdk.evidence import Evidence
from app.assessment_sdk.exceptions import (
    AssessmentError,
    AssessmentTimeoutError,
    ConfigurationError,
    ConnectionError,
    ExecutionError,
    ValidationError,
)
from app.assessment_sdk.finding import Finding
from app.assessment_sdk.http_client import AssessmentHttpClient
from app.assessment_sdk.metadata import AssessmentMetadata
from app.assessment_sdk.parser import ResponseParser
from app.assessment_sdk.prompt_templates import PromptTemplate, PromptTemplateRegistry
from app.assessment_sdk.recommendation import Recommendation
from app.assessment_sdk.result import AssessmentResult
from app.assessment_sdk.scoring import (
    calculate_confidence,
    calculate_overall_score,
    calculate_risk_score,
    normalize_score,
)
from app.assessment_sdk.severity import Severity, severity_rank

__all__ = [
    "AssessmentConfiguration",
    "AssessmentError",
    "AssessmentHttpClient",
    "AssessmentMetadata",
    "AssessmentResult",
    "AssessmentTimeoutError",
    "ConfigurationError",
    "ConnectionError",
    "Evidence",
    "ExecutionError",
    "Finding",
    "PromptTemplate",
    "PromptTemplateRegistry",
    "Recommendation",
    "ResponseParser",
    "Severity",
    "ValidationError",
    "calculate_confidence",
    "calculate_overall_score",
    "calculate_risk_score",
    "normalize_score",
    "severity_rank",
]
