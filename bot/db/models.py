"""SQLAlchemy database models."""

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class User(Base):
    """User model storing all bot users."""

    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("ix_users_joined_at", "joined_at"),)

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, username={self.username})>"


class Giveaway(Base):
    """Giveaway model storing giveaway configurations."""

    __tablename__ = "giveaways"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    start_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    num_winners: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    announce_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    announce_media_file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    announce_media_type: Mapped[str] = mapped_column(String(50), nullable=False, default="photo")
    created_by_admin_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("num_winners > 0", name="check_num_winners_positive"),
        CheckConstraint("end_at > start_at", name="check_end_after_start"),
        Index("ix_giveaways_is_active", "is_active"),
        Index("ix_giveaways_end_at", "end_at"),
    )

    def __repr__(self) -> str:
        return f"<Giveaway(id={self.id}, description={self.description[:30]}, is_active={self.is_active})>"


class Participant(Base):
    """Participant model tracking user participation in giveaways."""

    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    giveaway_id: Mapped[int] = mapped_column(nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    username_snapshot: Mapped[str | None] = mapped_column(String(255), nullable=True)
    giveaway_end_snapshot: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_participants_giveaway_user", "giveaway_id", "user_id", unique=True),
        Index("ix_participants_giveaway_id", "giveaway_id"),
        Index("ix_participants_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<Participant(id={self.id}, giveaway_id={self.giveaway_id}, user_id={self.user_id})>"


class Winner(Base):
    """Winner model storing selected winners with snapshot data."""

    __tablename__ = "winners"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    giveaway_id: Mapped[int] = mapped_column(nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    username_snapshot: Mapped[str | None] = mapped_column(String(255), nullable=True)
    giveaway_end_snapshot: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_winners_giveaway_user", "giveaway_id", "user_id", unique=True),
        Index("ix_winners_giveaway_id", "giveaway_id"),
    )

    def __repr__(self) -> str:
        return f"<Winner(id={self.id}, giveaway_id={self.giveaway_id}, user_id={self.user_id})>"


class AdminDraft(Base):
    """Admin draft model for persisting wizard progress."""

    __tablename__ = "admin_drafts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # "giveaway_create" or "broadcast"
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="in_progress"
    )  # "in_progress", "ready_preview", "cancelled"
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index(
            "ix_admin_drafts_active",
            "admin_id",
            "type",
            unique=True,
            postgresql_where=(status == "in_progress"),
        ),
        Index("ix_admin_drafts_updated_at", "updated_at"),
    )

    def __repr__(self) -> str:
        return f"<AdminDraft(id={self.id}, admin_id={self.admin_id}, type={self.type}, status={self.status})>"
