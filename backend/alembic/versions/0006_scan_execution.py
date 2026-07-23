"""extend scans/assessments for execution pipeline and add scan_summaries

Revision ID: 0006_scan_execution
Revises: 0005_connections
Create Date: 2026-07-23 23:50:00.000000
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006_scan_execution"
down_revision: str | None = "0005_connections"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DUMMY_CATALOG_ID = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeee1")


def upgrade() -> None:
    op.add_column("scans", sa.Column("connection_id", sa.Uuid(), nullable=True))
    op.add_column(
        "scans",
        sa.Column("progress_percent", sa.Float(), server_default="0", nullable=False),
    )
    op.add_column(
        "scans",
        sa.Column("completed_assessments", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "scans",
        sa.Column("failed_assessments", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column("scans", sa.Column("execution_time_ms", sa.Integer(), nullable=True))
    op.add_column(
        "scans",
        sa.Column(
            "cancel_requested",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.add_column("scans", sa.Column("error_message", sa.Text(), nullable=True))
    op.create_index("ix_scans_connection_id", "scans", ["connection_id"])
    op.create_foreign_key(
        "fk_scans_connection_id_connections",
        "scans",
        "connections",
        ["connection_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("assessments", sa.Column("execution_time_ms", sa.Integer(), nullable=True))
    op.add_column(
        "assessments",
        sa.Column(
            "raw_result",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "assessments",
        sa.Column(
            "logs",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )

    op.create_table(
        "scan_summaries",
        sa.Column("scan_id", sa.Uuid(), nullable=False),
        sa.Column("overall_score", sa.Float(), server_default="0", nullable=False),
        sa.Column("critical", sa.Integer(), server_default="0", nullable=False),
        sa.Column("high", sa.Integer(), server_default="0", nullable=False),
        sa.Column("medium", sa.Integer(), server_default="0", nullable=False),
        sa.Column("low", sa.Integer(), server_default="0", nullable=False),
        sa.Column("passed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_findings", sa.Integer(), server_default="0", nullable=False),
        sa.Column("execution_duration_ms", sa.Integer(), server_default="0", nullable=False),
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
        sa.UniqueConstraint("scan_id", name="uq_scan_summaries_scan_id"),
    )
    op.create_index("ix_scan_summaries_scan_id", "scan_summaries", ["scan_id"])

    catalog = sa.table(
        "assessment_catalog",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("slug", sa.String()),
        sa.column("category", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("architecture_support", postgresql.JSONB()),
        sa.column("default_weight", sa.Float()),
        sa.column("default_severity", sa.String()),
        sa.column("enabled", sa.Boolean()),
        sa.column("version", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    now = datetime.now(UTC)
    op.bulk_insert(
        catalog,
        [
            {
                "id": DUMMY_CATALOG_ID,
                "name": "Dummy Assessment",
                "slug": "dummy",
                "category": "custom",
                "description": (
                    "Orchestration validation assessment. Not a real security test. "
                    "Replaced by real engines in Sprint 8."
                ),
                "architecture_support": {"architectures": ["all"]},
                "default_weight": 0.0,
                "default_severity": "info",
                "enabled": True,
                "version": "0.1.0",
                "created_at": now,
                "updated_at": now,
            }
        ],
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM assessment_catalog WHERE slug = 'dummy'"))
    op.drop_index("ix_scan_summaries_scan_id", table_name="scan_summaries")
    op.drop_table("scan_summaries")
    op.drop_column("assessments", "logs")
    op.drop_column("assessments", "raw_result")
    op.drop_column("assessments", "execution_time_ms")
    op.drop_constraint("fk_scans_connection_id_connections", "scans", type_="foreignkey")
    op.drop_index("ix_scans_connection_id", table_name="scans")
    op.drop_column("scans", "error_message")
    op.drop_column("scans", "cancel_requested")
    op.drop_column("scans", "execution_time_ms")
    op.drop_column("scans", "failed_assessments")
    op.drop_column("scans", "completed_assessments")
    op.drop_column("scans", "progress_percent")
    op.drop_column("scans", "connection_id")
