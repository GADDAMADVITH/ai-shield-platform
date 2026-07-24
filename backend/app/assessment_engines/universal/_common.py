"""Shared helpers for universal assessment engines."""

from __future__ import annotations

import asyncio
import re
import time
from abc import ABC
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from app.assessment_engines.base import AssessmentEngine
from app.assessment_payloads.types import AssessmentPayload, PayloadLibrary
from app.assessment_sdk.configuration import AssessmentConfiguration
from app.assessment_sdk.evidence import Evidence
from app.assessment_sdk.finding import Finding
from app.assessment_sdk.http_client import AssessmentHttpClient
from app.assessment_sdk.metadata import AssessmentMetadata
from app.assessment_sdk.parser import ResponseParser
from app.assessment_sdk.recommendation import Recommendation
from app.assessment_sdk.result import AssessmentResult
from app.assessment_sdk.scoring import calculate_confidence, calculate_risk_score
from app.assessment_sdk.severity import Severity
from app.assessment_sdk.utils import truncate
from app.common.enums import AssessmentStatus, ConnectionMethod

if TYPE_CHECKING:
    from app.orchestration.context import ScanContext

REFUSAL_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bi\s+(?:cannot|can't|won't|will not|am not able to)\b",
        r"\bi'?m\s+(?:unable|not able|not allowed)\b",
        r"\bas an ai\b",
        r"\bagainst\s+(?:my|the)\s+(?:guidelines|policies|rules)\b",
        r"\bi\s+must\s+refuse\b",
        r"\bsorry,? but\b",
        r"\bi\s+cannot\s+comply\b",
        r"\bnot\s+able\s+to\s+(?:help|assist|provide)\b",
    )
)


@dataclass(slots=True)
class ProbeExchange:
    """One prompt/response exchange against the target application."""

    payload_id: str
    prompt: str
    response_text: str = ""
    status_code: int | None = None
    blocked: bool = False
    error: str | None = None
    raw: Any = None
    latency_ms: float | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and not self.blocked


PromptSender = Callable[[str], Awaitable[ProbeExchange]]


@dataclass(slots=True)
class TargetClient:
    """HTTP client that posts chat-style prompts to a connected application.

    Request shape (OpenAI-compatible chat completions):

    ``POST {base_url}`` with ``{"messages": [{"role": "user", "content": "..."}]}``

    Override the path via connection health_endpoint or context metadata key
    ``chat_path``. Unit tests may inject :class:`ScriptedTargetClient` instead.
    """

    http: AssessmentHttpClient
    endpoint: str
    timeout_seconds: float = 30.0
    max_response_chars: int = 500_000

    async def send_prompt(self, prompt: str, *, payload_id: str = "") -> ProbeExchange:
        started = time.perf_counter()
        try:
            response = await self.http.post(
                self.endpoint,
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "input": prompt,
                    "prompt": prompt,
                },
                timeout=self.timeout_seconds,
            )
            latency = (time.perf_counter() - started) * 1000
            text = _extract_response_text(response)
            text = truncate(text, max_chars=self.max_response_chars)
            blocked = response.status_code in {401, 403, 429} or (
                response.status_code >= 400 and not text
            )
            return ProbeExchange(
                payload_id=payload_id,
                prompt=prompt,
                response_text=text,
                status_code=response.status_code,
                blocked=blocked,
                raw={"status_code": response.status_code, "body": truncate(response.text)},
                latency_ms=latency,
            )
        except Exception as exc:  # noqa: BLE001 — engines convert to findings/errors
            latency = (time.perf_counter() - started) * 1000
            return ProbeExchange(
                payload_id=payload_id,
                prompt=prompt,
                error=str(exc) or exc.__class__.__name__,
                latency_ms=latency,
            )


@dataclass(slots=True)
class ScriptedTargetClient:
    """Deterministic target for unit tests — no network I/O."""

    responses: dict[str, str] = field(default_factory=dict)
    default_response: str = "I cannot comply with that request."
    status_code: int = 200
    blocked_ids: set[str] = field(default_factory=set)
    error_ids: set[str] = field(default_factory=set)

    async def send_prompt(self, prompt: str, *, payload_id: str = "") -> ProbeExchange:
        await asyncio.sleep(0)
        if payload_id in self.error_ids:
            return ProbeExchange(
                payload_id=payload_id,
                prompt=prompt,
                error="scripted transport error",
            )
        text = self.responses.get(payload_id)
        if text is None:
            text = self.responses.get(prompt, self.default_response)
        return ProbeExchange(
            payload_id=payload_id,
            prompt=prompt,
            response_text=text,
            status_code=self.status_code,
            blocked=payload_id in self.blocked_ids,
            raw={"scripted": True},
            latency_ms=0.0,
        )


def looks_like_refusal(text: str) -> bool:
    value = (text or "").strip()
    if not value:
        return False
    return any(p.search(value) for p in REFUSAL_PATTERNS)


def contains_signal(text: str, signal: str | None) -> bool:
    if not signal:
        return False
    return signal.lower() in (text or "").lower()


def _extract_response_text(response: Any) -> str:
    """Best-effort extraction from OpenAI-ish or plain HTTP bodies."""
    try:
        data = response.json()
    except Exception:  # noqa: BLE001
        return ResponseParser.as_text(getattr(response, "text", ""))

    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        for key in ("output", "response", "completion", "text", "content", "answer"):
            if key in data and data[key] is not None:
                return ResponseParser.as_text(data[key])
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict) and message.get("content") is not None:
                    return ResponseParser.as_text(message["content"])
                if first.get("text") is not None:
                    return ResponseParser.as_text(first["text"])
        return ResponseParser.as_text(data)
    return ResponseParser.as_text(data)


def resolve_config(
    context: ScanContext,
    default: AssessmentConfiguration | None = None,
) -> AssessmentConfiguration:
    """Merge engine default config with ``context.metadata['assessment_config']``."""
    base = default or AssessmentConfiguration()
    override = context.metadata.get("assessment_config")
    if not override:
        # Per-engine override keyed by assessment slug.
        keyed = context.metadata.get("assessment_configs")
        if isinstance(keyed, dict):
            override = keyed.get(getattr(context.catalog_entry, "slug", None))
    if isinstance(override, AssessmentConfiguration):
        return override
    if isinstance(override, dict):
        merged = {**base.to_dict(), **override}
        return AssessmentConfiguration.from_dict(merged)
    return base


def build_target_client(
    context: ScanContext,
    config: AssessmentConfiguration,
) -> TargetClient | ScriptedTargetClient:
    scripted = context.metadata.get("target_client")
    if scripted is not None:
        return scripted  # type: ignore[return-value]

    connection = context.connection
    base_url = getattr(connection, "base_url", None) or ""
    health = getattr(connection, "health_endpoint", None)
    chat_path = context.metadata.get("chat_path") or health or ""
    if chat_path and not str(chat_path).startswith("http"):
        endpoint = str(chat_path)
    elif base_url:
        endpoint = ""
    else:
        endpoint = "/"

    headers: dict[str, str] = {}
    raw_headers = getattr(connection, "headers", None) or {}
    if isinstance(raw_headers, dict):
        headers = {str(k): str(v) for k, v in raw_headers.items()}
    api_key = getattr(connection, "api_key", None)
    timeout = min(
        float(config.timeout_seconds),
        float(
            getattr(connection, "timeout_seconds", config.timeout_seconds)
            or config.timeout_seconds
        ),
    )
    http = AssessmentHttpClient.from_existing(context.http_client)
    # Prefer wrapping with auth when possible via raw client headers already set;
    # also allow explicit Authorization injection for one-off posts.
    if api_key and "Authorization" not in headers:
        headers["Authorization"] = f"Bearer {api_key}"

    class _HeaderClient(TargetClient):
        async def send_prompt(self, prompt: str, *, payload_id: str = "") -> ProbeExchange:
            started = time.perf_counter()
            try:
                response = await self.http.post(
                    self.endpoint or base_url or "/",
                    json={
                        "messages": [{"role": "user", "content": prompt}],
                        "input": prompt,
                        "prompt": prompt,
                    },
                    headers=headers or None,
                    timeout=self.timeout_seconds,
                )
                latency = (time.perf_counter() - started) * 1000
                text = truncate(
                    _extract_response_text(response),
                    max_chars=self.max_response_chars,
                )
                blocked = response.status_code in {401, 403, 429} or (
                    response.status_code >= 400 and not text
                )
                return ProbeExchange(
                    payload_id=payload_id,
                    prompt=prompt,
                    response_text=text,
                    status_code=response.status_code,
                    blocked=blocked,
                    raw={
                        "status_code": response.status_code,
                        "body": truncate(response.text),
                    },
                    latency_ms=latency,
                )
            except Exception as exc:  # noqa: BLE001
                return ProbeExchange(
                    payload_id=payload_id,
                    prompt=prompt,
                    error=str(exc) or exc.__class__.__name__,
                    latency_ms=(time.perf_counter() - started) * 1000,
                )

    return _HeaderClient(
        http=http,
        endpoint=str(endpoint) if endpoint else (base_url or "/"),
        timeout_seconds=timeout,
        max_response_chars=config.max_response_chars,
    )


class UniversalAssessmentEngine(AssessmentEngine, ABC):
    """Base class for Sprint 9 universal security assessments."""

    VERSION = "1.0.0"
    CATEGORY = "universal"

    def __init__(
        self,
        *,
        config: AssessmentConfiguration | None = None,
        target_client: TargetClient | ScriptedTargetClient | None = None,
    ) -> None:
        self._default_config = config or AssessmentConfiguration()
        self._injected_target = target_client

    @property
    def version(self) -> str:
        return self.VERSION

    def supported_connection_methods(self) -> frozenset[ConnectionMethod]:
        return frozenset(ConnectionMethod)

    def payload_library(self) -> PayloadLibrary:
        raise NotImplementedError

    def select_payloads(
        self,
        config: AssessmentConfiguration,
    ) -> list[AssessmentPayload]:
        library = self.payload_library()
        selection = config.select_payload_ids(library.ids())
        return library.select(selection)

    async def run(self, context: ScanContext) -> AssessmentResult:
        started = time.perf_counter()
        config = resolve_config(context, self._default_config)
        if not config.enabled:
            evidence = Evidence(extra={"skipped": True, "reason": "disabled"})
            evidence.add_log("Assessment disabled by configuration", level="info")
            return AssessmentResult(
                status=AssessmentStatus.SKIPPED,
                assessment_name=self.name,
                assessment_version=self.version,
                risk_score=0.0,
                confidence=1.0,
                severity=Severity.INFO,
                evidence=evidence,
                metadata=self._metadata(context, config, extra={"enabled": False}),
                execution_time_ms=(time.perf_counter() - started) * 1000,
            )

        payloads = self.select_payloads(config)
        target = self._injected_target or build_target_client(context, config)
        try:
            result = await self.execute(
                context,
                config=config,
                payloads=payloads,
                target=target,
            )
        except Exception as exc:  # noqa: BLE001
            return AssessmentResult.error(
                assessment_name=self.name,
                assessment_version=self.version,
                message=str(exc) or exc.__class__.__name__,
                metadata=self._metadata(context, config),
                execution_time_ms=(time.perf_counter() - started) * 1000,
            )
        if result.execution_time_ms is None:
            result.execution_time_ms = (time.perf_counter() - started) * 1000
        return result

    async def execute(
        self,
        context: ScanContext,
        *,
        config: AssessmentConfiguration,
        payloads: Sequence[AssessmentPayload],
        target: TargetClient | ScriptedTargetClient,
    ) -> AssessmentResult:
        raise NotImplementedError

    async def probe_all(
        self,
        payloads: Sequence[AssessmentPayload],
        target: TargetClient | ScriptedTargetClient,
        *,
        retry_attempts: int = 0,
        retry_backoff_seconds: float = 1.0,
    ) -> list[ProbeExchange]:
        exchanges: list[ProbeExchange] = []
        for payload in payloads:
            exchange = await self._probe_with_retry(
                payload,
                target,
                retry_attempts=retry_attempts,
                retry_backoff_seconds=retry_backoff_seconds,
            )
            exchanges.append(exchange)
        return exchanges

    async def _probe_with_retry(
        self,
        payload: AssessmentPayload,
        target: TargetClient | ScriptedTargetClient,
        *,
        retry_attempts: int,
        retry_backoff_seconds: float,
    ) -> ProbeExchange:
        attempts = max(0, retry_attempts) + 1
        last: ProbeExchange | None = None
        for attempt in range(attempts):
            last = await target.send_prompt(payload.prompt, payload_id=payload.id)
            if last.error is None:
                return last
            if attempt + 1 < attempts:
                await asyncio.sleep(retry_backoff_seconds * (attempt + 1))
        assert last is not None
        return last

    def finalize(
        self,
        *,
        context: ScanContext,
        config: AssessmentConfiguration,
        findings: list[Finding],
        recommendations: list[Recommendation] | None = None,
        evidence: Evidence | None = None,
        raw_output: Any = None,
        confidence_samples: Sequence[float] | None = None,
        execution_time_ms: float | None = None,
    ) -> AssessmentResult:
        """Build passed/failed result using SDK scoring only."""
        actionable = [
            f for f in findings if config.meets_severity_threshold(f.severity)
        ]
        risk = calculate_risk_score([f.severity for f in actionable])
        confidence = calculate_confidence(
            confidence_samples
            or [f.confidence for f in actionable if f.confidence is not None],
            default=0.8 if actionable else 0.9,
        )
        evidence = evidence or Evidence()
        meta = self._metadata(
            context,
            config,
            extra={
                "finding_count": len(findings),
                "actionable_finding_count": len(actionable),
                "payload_selection": config.payload_selection,
            },
        )
        if not actionable:
            return AssessmentResult.passed(
                assessment_name=self.name,
                assessment_version=self.version,
                risk_score=risk,
                confidence=confidence,
                severity=Severity.INFO,
                evidence=evidence,
                recommendations=recommendations
                or [
                    Recommendation(
                        title="No issues detected",
                        description=f"{self.name} completed without actionable findings.",
                        priority=Severity.INFO,
                    )
                ],
                metadata=meta,
                execution_time_ms=execution_time_ms,
                raw_output=raw_output,
            )
        return AssessmentResult.failed(
            assessment_name=self.name,
            assessment_version=self.version,
            findings=actionable,
            risk_score=risk,
            confidence=confidence,
            recommendations=recommendations
            or [
                Recommendation(
                    title="Remediate detected weaknesses",
                    description=(
                        f"{self.name} found {len(actionable)} actionable issue(s). "
                        "Review findings and harden prompt/input/output controls."
                    ),
                    priority=actionable[0].severity,
                    mitigation_steps=[
                        f.recommendation
                        for f in actionable
                        if f.recommendation
                    ][:5],
                )
            ],
            evidence=evidence,
            metadata=meta,
            execution_time_ms=execution_time_ms,
            raw_output=raw_output,
        )

    def _metadata(
        self,
        context: ScanContext,
        config: AssessmentConfiguration,
        *,
        extra: dict[str, Any] | None = None,
    ) -> AssessmentMetadata:
        return AssessmentMetadata(
            version=self.version,
            author="ai-shield",
            engine=self.name,
            execution_environment=getattr(context.settings, "app_env", None),
            extra={
                "category": self.CATEGORY,
                "assessment_key": self.assessment_key,
                "config": config.to_dict(),
                **(extra or {}),
            },
        )


def exchange_evidence(exchange: ProbeExchange) -> Evidence:
    return Evidence(
        prompt=truncate(exchange.prompt, max_chars=4_000),
        completion=truncate(exchange.response_text, max_chars=4_000),
        request={"payload_id": exchange.payload_id},
        response={
            "status_code": exchange.status_code,
            "blocked": exchange.blocked,
            "error": exchange.error,
        },
        extra={
            "latency_ms": exchange.latency_ms,
            "raw": exchange.raw,
        },
    )
