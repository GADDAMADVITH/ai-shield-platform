"""Seed data for the Assessment Catalog."""

from __future__ import annotations

from typing import Any, TypedDict

from app.common.enums import AssessmentCategory, Severity


class CatalogSeed(TypedDict):
    name: str
    slug: str
    category: str
    description: str
    architecture_support: dict[str, Any]
    default_weight: float
    default_severity: str
    enabled: bool
    version: str


def _entry(
    *,
    name: str,
    slug: str,
    category: AssessmentCategory,
    description: str,
    architectures: list[str],
    default_severity: Severity,
    default_weight: float = 1.0,
    enabled: bool = True,
    version: str = "1.0.0",
) -> CatalogSeed:
    return {
        "name": name,
        "slug": slug,
        "category": category.value,
        "description": description,
        "architecture_support": {"architectures": architectures},
        "default_weight": default_weight,
        "default_severity": default_severity.value,
        "enabled": enabled,
        "version": version,
    }


ASSESSMENT_CATALOG_SEED: list[CatalogSeed] = [
    # --- Universal ---
    _entry(
        name="Prompt Injection",
        slug="prompt-injection",
        category=AssessmentCategory.UNIVERSAL,
        description=(
            "Detects attempts to override system instructions or coerce the model "
            "into following attacker-controlled prompts."
        ),
        architectures=["universal", "rag", "agent", "coding", "api"],
        default_severity=Severity.HIGH,
        default_weight=1.2,
    ),
    _entry(
        name="Jailbreak",
        slug="jailbreak",
        category=AssessmentCategory.UNIVERSAL,
        description=(
            "Evaluates resilience against persona switches, DAN-style bypasses, "
            "and other techniques that disable safety constraints."
        ),
        architectures=["universal", "rag", "agent", "coding", "api"],
        default_severity=Severity.HIGH,
        default_weight=1.2,
    ),
    _entry(
        name="Prompt Leakage",
        slug="prompt-leakage",
        category=AssessmentCategory.UNIVERSAL,
        description=(
            "Checks whether system prompts, hidden policies, or internal instructions "
            "can be extracted through crafted queries."
        ),
        architectures=["universal", "rag", "agent", "coding", "api"],
        default_severity=Severity.HIGH,
        default_weight=1.1,
    ),
    _entry(
        name="Sensitive Data Leakage",
        slug="sensitive-data-leakage",
        category=AssessmentCategory.UNIVERSAL,
        description=(
            "Identifies exposure of PII, secrets, credentials, or other sensitive "
            "data in model outputs."
        ),
        architectures=["universal", "rag", "agent", "coding", "api"],
        default_severity=Severity.CRITICAL,
        default_weight=1.3,
    ),
    _entry(
        name="Hallucination",
        slug="hallucination",
        category=AssessmentCategory.UNIVERSAL,
        description=(
            "Measures fabrication of facts, citations, or unsupported claims that "
            "could mislead users."
        ),
        architectures=["universal", "rag", "agent", "coding", "api"],
        default_severity=Severity.MEDIUM,
        default_weight=1.0,
    ),
    _entry(
        name="Output Validation",
        slug="output-validation",
        category=AssessmentCategory.UNIVERSAL,
        description=(
            "Validates that responses adhere to expected schemas, content policies, "
            "and safe output formats."
        ),
        architectures=["universal", "rag", "agent", "coding", "api"],
        default_severity=Severity.MEDIUM,
        default_weight=1.0,
    ),
    _entry(
        name="Prompt Robustness",
        slug="prompt-robustness",
        category=AssessmentCategory.UNIVERSAL,
        description=(
            "Assesses stability under paraphrasing, noise, multilingual variants, "
            "and adversarial prompt perturbations."
        ),
        architectures=["universal", "rag", "agent", "coding", "api"],
        default_severity=Severity.MEDIUM,
        default_weight=0.9,
    ),
    _entry(
        name="Rate Limiting",
        slug="rate-limiting",
        category=AssessmentCategory.UNIVERSAL,
        description=(
            "Verifies abuse controls that limit excessive requests, token burn, "
            "or automated probing."
        ),
        architectures=["universal", "api", "agent"],
        default_severity=Severity.MEDIUM,
        default_weight=0.8,
    ),
    _entry(
        name="Authentication & Authorization",
        slug="authentication-authorization",
        category=AssessmentCategory.UNIVERSAL,
        description=(
            "Tests whether protected AI capabilities enforce authentication and "
            "correct authorization boundaries."
        ),
        architectures=["universal", "api", "agent"],
        default_severity=Severity.CRITICAL,
        default_weight=1.3,
    ),
    _entry(
        name="Input Validation",
        slug="input-validation",
        category=AssessmentCategory.UNIVERSAL,
        description=(
            "Checks sanitization and rejection of malformed, oversized, or "
            "malicious user inputs before model invocation."
        ),
        architectures=["universal", "rag", "agent", "coding", "api"],
        default_severity=Severity.HIGH,
        default_weight=1.0,
    ),
    # --- RAG ---
    _entry(
        name="RAG Poisoning",
        slug="rag-poisoning",
        category=AssessmentCategory.RAG,
        description=(
            "Detects whether poisoned or adversarial documents in the knowledge base "
            "can manipulate retrieval-augmented answers."
        ),
        architectures=["rag"],
        default_severity=Severity.HIGH,
        default_weight=1.2,
    ),
    _entry(
        name="Vector Database Security",
        slug="vector-database-security",
        category=AssessmentCategory.RAG,
        description=(
            "Evaluates access control, isolation, and exposure risks around vector "
            "stores and embedding indexes."
        ),
        architectures=["rag"],
        default_severity=Severity.HIGH,
        default_weight=1.1,
    ),
    _entry(
        name="Retrieval Leakage",
        slug="retrieval-leakage",
        category=AssessmentCategory.RAG,
        description=(
            "Checks whether retrieval pipelines leak confidential chunks or "
            "cross-tenant documents into responses."
        ),
        architectures=["rag"],
        default_severity=Severity.CRITICAL,
        default_weight=1.3,
    ),
    _entry(
        name="Embedding Security",
        slug="embedding-security",
        category=AssessmentCategory.RAG,
        description=(
            "Assesses embedding inversion, similarity abuse, and adversarial "
            "embedding manipulation risks."
        ),
        architectures=["rag"],
        default_severity=Severity.MEDIUM,
        default_weight=1.0,
    ),
    # --- Agent ---
    _entry(
        name="Agent Tool Abuse",
        slug="agent-tool-abuse",
        category=AssessmentCategory.AGENT,
        description=(
            "Tests whether agents can be coerced into misusing connected tools "
            "beyond intended scopes."
        ),
        architectures=["agent"],
        default_severity=Severity.CRITICAL,
        default_weight=1.3,
    ),
    _entry(
        name="Function Calling Abuse",
        slug="function-calling-abuse",
        category=AssessmentCategory.AGENT,
        description=(
            "Evaluates unsafe or unauthorized function/tool invocations through "
            "crafted natural-language instructions."
        ),
        architectures=["agent", "api"],
        default_severity=Severity.HIGH,
        default_weight=1.2,
    ),
    _entry(
        name="Tool Injection",
        slug="tool-injection",
        category=AssessmentCategory.AGENT,
        description=(
            "Detects injection into tool arguments, schemas, or orchestration "
            "channels that alter agent behavior."
        ),
        architectures=["agent"],
        default_severity=Severity.HIGH,
        default_weight=1.2,
    ),
    _entry(
        name="Memory Leakage",
        slug="memory-leakage",
        category=AssessmentCategory.AGENT,
        description=(
            "Checks whether agent memory stores leak prior-session secrets, "
            "PII, or cross-user context."
        ),
        architectures=["agent"],
        default_severity=Severity.HIGH,
        default_weight=1.1,
    ),
    # --- Coding ---
    _entry(
        name="Code Execution Safety",
        slug="code-execution-safety",
        category=AssessmentCategory.CODING,
        description=(
            "Assesses sandboxing and controls when AI systems generate or execute "
            "code on behalf of users."
        ),
        architectures=["coding", "agent"],
        default_severity=Severity.CRITICAL,
        default_weight=1.3,
    ),
    _entry(
        name="SQL Injection",
        slug="sql-injection",
        category=AssessmentCategory.CODING,
        description=(
            "Tests whether AI-generated queries or tool-backed database access "
            "are vulnerable to SQL injection."
        ),
        architectures=["coding", "api", "agent"],
        default_severity=Severity.CRITICAL,
        default_weight=1.3,
    ),
    _entry(
        name="Command Injection",
        slug="command-injection",
        category=AssessmentCategory.CODING,
        description=(
            "Detects OS command injection risks via generated shell commands or "
            "tool wrappers."
        ),
        architectures=["coding", "agent"],
        default_severity=Severity.CRITICAL,
        default_weight=1.3,
    ),
    # --- API ---
    _entry(
        name="API Security",
        slug="api-security",
        category=AssessmentCategory.API,
        description=(
            "Evaluates authentication, authorization, input handling, and abuse "
            "controls on AI-facing API surfaces."
        ),
        architectures=["api"],
        default_severity=Severity.HIGH,
        default_weight=1.1,
    ),
    # --- Custom ---
    _entry(
        name="Custom Assessment",
        slug="custom-assessment",
        category=AssessmentCategory.CUSTOM,
        description=(
            "Reserved catalog entry for organization-defined assessment workflows "
            "and custom security tests."
        ),
        architectures=["universal", "rag", "agent", "coding", "api", "vision", "audio", "custom"],
        default_severity=Severity.MEDIUM,
        default_weight=1.0,
        enabled=True,
    ),
]
