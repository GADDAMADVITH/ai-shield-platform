"""ORM model package.

Importing this package registers all models on ``Base.metadata``.
"""

from app.models.assessment import Assessment
from app.models.assessment_catalog import AssessmentCatalog
from app.models.audit_log import AuditLog
from app.models.connection import Connection
from app.models.notification import Notification
from app.models.project import Project
from app.models.report import Report
from app.models.scan import Scan
from app.models.scan_summary import ScanSummary
from app.models.user import User

__all__ = [
    "Assessment",
    "AssessmentCatalog",
    "AuditLog",
    "Connection",
    "Notification",
    "Project",
    "Report",
    "Scan",
    "ScanSummary",
    "User",
]
