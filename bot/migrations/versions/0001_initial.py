"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-22

This migration mirrors the schema that ``Base.metadata.create_all`` used to
produce, so an existing server database can be marked as up-to-date with
``alembic stamp head`` WITHOUT recreating any tables (no data loss). Fresh
databases get the full schema via ``alembic upgrade head``.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Idempotent baseline: if the schema already exists (a server DB that was
    # previously created by metadata.create_all, without an alembic_version
    # table), do NOT recreate anything — just record this revision as applied.
    # This makes `alembic upgrade head` safe to run automatically on first
    # deploy against an existing production database (no data loss).
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("users"):
        return

    # --- users ---
    op.create_table(
        "users",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column(
            "joined_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index("ix_users_user_id", "users", ["user_id"])
    op.create_index("ix_users_joined_at", "users", ["joined_at"])

    # --- giveaways ---
    op.create_table(
        "giveaways",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("start_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("end_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("num_winners", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("announce_text", sa.Text(), nullable=True),
        sa.Column("announce_media_file_id", sa.String(length=255), nullable=False),
        sa.Column("announce_media_type", sa.String(length=50), nullable=False),
        sa.Column("created_by_admin_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("ended_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("num_winners > 0", name="check_num_winners_positive"),
        sa.CheckConstraint("end_at > start_at", name="check_end_after_start"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_giveaways_is_active", "giveaways", ["is_active"])
    op.create_index("ix_giveaways_end_at", "giveaways", ["end_at"])

    # --- participants ---
    op.create_table(
        "participants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("giveaway_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "joined_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("username_snapshot", sa.String(length=255), nullable=True),
        sa.Column("giveaway_end_snapshot", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_participants_giveaway_user", "participants", ["giveaway_id", "user_id"], unique=True
    )
    op.create_index("ix_participants_giveaway_id", "participants", ["giveaway_id"])
    op.create_index("ix_participants_user_id", "participants", ["user_id"])

    # --- winners ---
    op.create_table(
        "winners",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("giveaway_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("username_snapshot", sa.String(length=255), nullable=True),
        sa.Column("giveaway_end_snapshot", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_winners_giveaway_user", "winners", ["giveaway_id", "user_id"], unique=True)
    op.create_index("ix_winners_giveaway_id", "winners", ["giveaway_id"])

    # --- admin_drafts ---
    op.create_table(
        "admin_drafts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("admin_id", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_admin_drafts_active",
        "admin_drafts",
        ["admin_id", "type"],
        unique=True,
        postgresql_where=sa.text("status = 'in_progress'"),
    )
    op.create_index("ix_admin_drafts_updated_at", "admin_drafts", ["updated_at"])


def downgrade() -> None:
    op.drop_table("admin_drafts")
    op.drop_index("ix_winners_giveaway_id", table_name="winners")
    op.drop_index("ix_winners_giveaway_user", table_name="winners")
    op.drop_table("winners")
    op.drop_index("ix_participants_user_id", table_name="participants")
    op.drop_index("ix_participants_giveaway_id", table_name="participants")
    op.drop_index("ix_participants_giveaway_user", table_name="participants")
    op.drop_table("participants")
    op.drop_index("ix_giveaways_end_at", table_name="giveaways")
    op.drop_index("ix_giveaways_is_active", table_name="giveaways")
    op.drop_table("giveaways")
    op.drop_index("ix_users_joined_at", table_name="users")
    op.drop_index("ix_users_user_id", table_name="users")
    op.drop_table("users")
