"""Domain enumerations used across models and schemas."""

from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class ProjectEnvironment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ProjectStatus(StrEnum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    ARCHIVED = "archived"


class ConnectionMethod(StrEnum):
    REST_API = "rest_api"
    OPENAPI = "openapi"
    LOCALHOST = "localhost"
    PLAYWRIGHT = "playwright"
    SDK = "sdk"
    WEBHOOK = "webhook"


class ConnectionStatus(StrEnum):
    UNVERIFIED = "unverified"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    ERROR = "error"


class ScanStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AssessmentStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class AssessmentCategory(StrEnum):
    """High-level catalog groupings for security assessments."""

    UNIVERSAL = "universal"
    RAG = "rag"
    AGENT = "agent"
    CODING = "coding"
    API = "api"
    VISION = "vision"
    AUDIO = "audio"
    CUSTOM = "custom"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class NotificationType(StrEnum):
    SECURITY = "security"
    SYSTEM = "system"
    REPORTS = "reports"
    PROJECTS = "projects"


class ReportStatus(StrEnum):
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class AuditAction(StrEnum):
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"
    CONNECTION_CREATED = "connection_created"
    CONNECTION_UPDATED = "connection_updated"
    CONNECTION_DELETED = "connection_deleted"
    CONNECTION_TESTED = "connection_tested"
    SCAN_STARTED = "scan_started"
    SCAN_COMPLETED = "scan_completed"
    SCAN_FAILED = "scan_failed"
    REPORT_GENERATED = "report_generated"
    REPORT_DOWNLOADED = "report_downloaded"
    SETTINGS_UPDATED = "settings_updated"
