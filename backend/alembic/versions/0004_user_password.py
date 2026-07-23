"""add users.hashed_password for authentication

Revision ID: 0004_user_password
Revises: 0003_assessment_catalog
Create Date: 2026-07-23 17:20:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_user_password"
down_revision: str | None = "0003_assessment_catalog"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Foundation stage: no production users yet. Empty-table NOT NULL add is safe.
    op.execute(sa.text("DELETE FROM users"))
    op.add_column(
        "users",
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "hashed_password")
