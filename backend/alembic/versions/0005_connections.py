"""add connections table for project connection management

Revision ID: 0005_connections
Revises: 0004_user_password
Create Date: 2026-07-23 17:45:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0005_connections"
down_revision: str | None = "0004_user_password"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "connections",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("connection_method", sa.String(length=64), nullable=False),
        sa.Column("base_url", sa.String(length=2048), nullable=True),
        sa.Column("health_endpoint", sa.String(length=2048), nullable=True),
        sa.Column("api_key", sa.String(length=2048), nullable=True),
        sa.Column(
            "headers",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("timeout_seconds", sa.Integer(), server_default="10", nullable=False),
        sa.Column("verify_ssl", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("playwright_entry_url", sa.String(length=2048), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="unverified",
            nullable=False,
        ),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "name", name="uq_connections_project_id_name"),
    )
    op.create_index(op.f("ix_connections_project_id"), "connections", ["project_id"], unique=False)
    op.create_index(
        op.f("ix_connections_connection_method"),
        "connections",
        ["connection_method"],
        unique=False,
    )
    op.create_index(op.f("ix_connections_status"), "connections", ["status"], unique=False)
    op.create_index(
        "ix_connections_project_id_status",
        "connections",
        ["project_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_connections_project_id_status", table_name="connections")
    op.drop_index(op.f("ix_connections_status"), table_name="connections")
    op.drop_index(op.f("ix_connections_connection_method"), table_name="connections")
    op.drop_index(op.f("ix_connections_project_id"), table_name="connections")
    op.drop_table("connections")
