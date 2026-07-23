"""assessment catalog: source of truth for security tests + link assessments

Revision ID: 0003_assessment_catalog
Revises: 0002_multi_assessment
Create Date: 2026-07-23 17:00:00.000000
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.db.seeds.assessment_catalog import ASSESSMENT_CATALOG_SEED

# revision identifiers, used by Alembic.
revision: str = "0003_assessment_catalog"
down_revision: str | None = "0002_multi_assessment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assessment_catalog",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "architecture_support",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("default_weight", sa.Float(), server_default="1.0", nullable=False),
        sa.Column(
            "default_severity",
            sa.String(length=32),
            server_default="medium",
            nullable=False,
        ),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("version", sa.String(length=32), server_default="1.0.0", nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(
        op.f("ix_assessment_catalog_slug"),
        "assessment_catalog",
        ["slug"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assessment_catalog_category"),
        "assessment_catalog",
        ["category"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assessment_catalog_enabled"),
        "assessment_catalog",
        ["enabled"],
        unique=False,
    )
    op.create_index(
        "ix_assessment_catalog_category_enabled",
        "assessment_catalog",
        ["category", "enabled"],
        unique=False,
    )

    # Seed catalog — source of truth for available assessments.
    catalog_table = sa.table(
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
    )
    op.bulk_insert(
        catalog_table,
        [
            {
                "id": uuid.uuid4(),
                "name": entry["name"],
                "slug": entry["slug"],
                "category": entry["category"],
                "description": entry["description"],
                "architecture_support": entry["architecture_support"],
                "default_weight": entry["default_weight"],
                "default_severity": entry["default_severity"],
                "enabled": entry["enabled"],
                "version": entry["version"],
            }
            for entry in ASSESSMENT_CATALOG_SEED
        ],
    )

    # Replace denormalized test fields with catalog FK.
    # No production assessment rows expected at this foundation stage.
    op.execute(sa.text("DELETE FROM assessments"))

    op.drop_index("ix_assessments_category_severity", table_name="assessments")
    op.drop_index(op.f("ix_assessments_test_category"), table_name="assessments")
    op.drop_constraint("uq_assessments_scan_id_test_name", "assessments", type_="unique")
    op.drop_column("assessments", "test_name")
    op.drop_column("assessments", "test_category")

    op.add_column(
        "assessments",
        sa.Column("assessment_catalog_id", sa.Uuid(), nullable=False),
    )
    op.create_foreign_key(
        "fk_assessments_assessment_catalog_id",
        "assessments",
        "assessment_catalog",
        ["assessment_catalog_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        op.f("ix_assessments_assessment_catalog_id"),
        "assessments",
        ["assessment_catalog_id"],
        unique=False,
    )
    op.create_index(
        "ix_assessments_catalog_id_status",
        "assessments",
        ["assessment_catalog_id", "status"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_assessments_scan_id_catalog_id",
        "assessments",
        ["scan_id", "assessment_catalog_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_assessments_scan_id_catalog_id", "assessments", type_="unique")
    op.drop_index("ix_assessments_catalog_id_status", table_name="assessments")
    op.drop_index(op.f("ix_assessments_assessment_catalog_id"), table_name="assessments")
    op.drop_constraint("fk_assessments_assessment_catalog_id", "assessments", type_="foreignkey")
    op.drop_column("assessments", "assessment_catalog_id")

    op.add_column(
        "assessments",
        sa.Column("test_name", sa.String(length=255), nullable=False, server_default="unknown"),
    )
    op.add_column(
        "assessments",
        sa.Column(
            "test_category",
            sa.String(length=64),
            nullable=False,
            server_default="other",
        ),
    )
    op.create_unique_constraint(
        "uq_assessments_scan_id_test_name",
        "assessments",
        ["scan_id", "test_name"],
    )
    op.create_index(
        op.f("ix_assessments_test_category"),
        "assessments",
        ["test_category"],
        unique=False,
    )
    op.create_index(
        "ix_assessments_category_severity",
        "assessments",
        ["test_category", "severity"],
        unique=False,
    )
    op.alter_column("assessments", "test_name", server_default=None)
    op.alter_column("assessments", "test_category", server_default=None)

    op.drop_index("ix_assessment_catalog_category_enabled", table_name="assessment_catalog")
    op.drop_index(op.f("ix_assessment_catalog_enabled"), table_name="assessment_catalog")
    op.drop_index(op.f("ix_assessment_catalog_category"), table_name="assessment_catalog")
    op.drop_index(op.f("ix_assessment_catalog_slug"), table_name="assessment_catalog")
    op.drop_table("assessment_catalog")
