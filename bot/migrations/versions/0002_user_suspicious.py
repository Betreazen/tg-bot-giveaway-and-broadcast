"""add users.is_suspicious

Revision ID: 0002_user_suspicious
Revises: 0001_initial
Create Date: 2026-06-26

Adds a flag for admin-marked suspicious accounts (may participate, never win).
Adding a boolean column with a server_default is a metadata-only change on
PostgreSQL 11+, so it is fast and safe even on a large users table.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_user_suspicious"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("users")}
    if "is_suspicious" not in columns:
        op.add_column(
            "users",
            sa.Column("is_suspicious", sa.Boolean(), server_default="false", nullable=False),
        )


def downgrade() -> None:
    op.drop_column("users", "is_suspicious")
