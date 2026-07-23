"""multi-assessment architecture: assessments, audit_logs, detach reports from assessment_results

Revision ID: 0002_multi_assessment
Revises: 0001_initial_schema
Create Date: 2026-07-23 16:45:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_multi_assessment"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Reports aggregate via Scan — remove direct AssessmentResult dependency.
    op.drop_index(op.f("ix_reports_assessment_result_id"), table_name="reports")
    op.drop_constraint(
        "reports_assessment_result_id_fkey",
        "reports",
        type_="foreignkey",
    )
    op.drop_column("reports", "assessment_result_id")

    # Replace 1:1 assessment_results with 1:N assessments.
    op.drop_index(op.f("ix_assessment_results_scan_id"), table_name="assessment_results")
    op.drop_index(op.f("ix_assessment_results_risk_level"), table_name="assessment_results")
    op.drop_table("assessment_results")

    op.create_table(
        "assessments",
        sa.Column("scan_id", sa.Uuid(), nullable=False),
        sa.Column("test_name", sa.String(length=255), nullable=False),
        sa.Column("test_category", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=64), server_default="pending", nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("finding_summary", sa.Text(), nullable=True),
        sa.Column(
            "evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scan_id", "test_name", name="uq_assessments_scan_id_test_name"),
    )
    op.create_index(op.f("ix_assessments_scan_id"), "assessments", ["scan_id"], unique=False)
    op.create_index(op.f("ix_assessments_status"), "assessments", ["status"], unique=False)
    op.create_index(op.f("ix_assessments_severity"), "assessments", ["severity"], unique=False)
    op.create_index(
        op.f("ix_assessments_test_category"),
        "assessments",
        ["test_category"],
        unique=False,
    )
    op.create_index(
        "ix_assessments_scan_id_status",
        "assessments",
        ["scan_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_assessments_scan_id_severity",
        "assessments",
        ["scan_id", "severity"],
        unique=False,
    )
    op.create_index(
        "ix_assessments_category_severity",
        "assessments",
        ["test_category", "severity"],
        unique=False,
    )

    op.create_table(
        "audit_logs",
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("scan_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_project_id"), "audit_logs", ["project_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_scan_id"), "audit_logs", ["scan_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_resource"), "audit_logs", ["resource"], unique=False)
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"], unique=False)
    op.create_index(
        "ix_audit_logs_user_id_created_at",
        "audit_logs",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_action_created_at",
        "audit_logs",
        ["action", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_resource_created_at",
        "audit_logs",
        ["resource", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_resource_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id_created_at", table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_created_at"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_resource"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_scan_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_project_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_assessments_category_severity", table_name="assessments")
    op.drop_index("ix_assessments_scan_id_severity", table_name="assessments")
    op.drop_index("ix_assessments_scan_id_status", table_name="assessments")
    op.drop_index(op.f("ix_assessments_test_category"), table_name="assessments")
    op.drop_index(op.f("ix_assessments_severity"), table_name="assessments")
    op.drop_index(op.f("ix_assessments_status"), table_name="assessments")
    op.drop_index(op.f("ix_assessments_scan_id"), table_name="assessments")
    op.drop_table("assessments")

    op.create_table(
        "assessment_results",
        sa.Column("scan_id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("grade", sa.String(length=16), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.Column(
            "summary",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "findings",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "breakdown",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scan_id"),
    )
    op.create_index(
        op.f("ix_assessment_results_risk_level"),
        "assessment_results",
        ["risk_level"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assessment_results_scan_id"),
        "assessment_results",
        ["scan_id"],
        unique=False,
    )

    op.add_column("reports", sa.Column("assessment_result_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "reports_assessment_result_id_fkey",
        "reports",
        "assessment_results",
        ["assessment_result_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_reports_assessment_result_id"),
        "reports",
        ["assessment_result_id"],
        unique=False,
    )
