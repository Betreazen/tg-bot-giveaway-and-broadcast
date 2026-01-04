"""Admin draft repository for CRUD operations."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import AdminDraft


async def create_draft(
    session: AsyncSession, admin_id: int, draft_type: str, payload: dict[str, Any]
) -> AdminDraft:
    """
    Create new admin draft.

    Args:
        session: Database session
        admin_id: Admin user ID
        draft_type: Draft type ("giveaway_create" or "broadcast")
        payload: Draft data

    Returns:
        Created AdminDraft object
    """
    draft = AdminDraft(admin_id=admin_id, type=draft_type, payload=payload, status="in_progress")
    session.add(draft)
    await session.flush()
    return draft


async def get_draft(session: AsyncSession, admin_id: int, draft_type: str) -> AdminDraft | None:
    """
    Get active draft for admin by type.

    Args:
        session: Database session
        admin_id: Admin user ID
        draft_type: Draft type

    Returns:
        AdminDraft object if found, None otherwise
    """
    result = await session.execute(
        select(AdminDraft).where(
            AdminDraft.admin_id == admin_id, AdminDraft.type == draft_type, AdminDraft.status == "in_progress"
        )
    )
    return result.scalar_one_or_none()


async def update_draft(
    session: AsyncSession, draft_id: int, payload: dict[str, Any] | None = None, status: str | None = None
) -> AdminDraft | None:
    """
    Update draft payload and/or status.

    Args:
        session: Database session
        draft_id: Draft ID
        payload: New payload data (optional)
        status: New status (optional)

    Returns:
        Updated AdminDraft object if found, None otherwise
    """
    result = await session.execute(select(AdminDraft).where(AdminDraft.id == draft_id))
    draft = result.scalar_one_or_none()

    if draft:
        if payload is not None:
            draft.payload = payload
        if status is not None:
            draft.status = status
        draft.updated_at = datetime.utcnow()
        await session.flush()

    return draft


async def delete_draft(session: AsyncSession, draft_id: int) -> bool:
    """
    Delete draft by ID.

    Args:
        session: Database session
        draft_id: Draft ID

    Returns:
        True if deleted, False if not found
    """
    result = await session.execute(delete(AdminDraft).where(AdminDraft.id == draft_id))
    await session.flush()
    return result.rowcount > 0


async def delete_draft_by_admin(session: AsyncSession, admin_id: int, draft_type: str) -> bool:
    """
    Delete draft by admin ID and type.

    Args:
        session: Database session
        admin_id: Admin user ID
        draft_type: Draft type

    Returns:
        True if deleted, False if not found
    """
    result = await session.execute(
        delete(AdminDraft).where(AdminDraft.admin_id == admin_id, AdminDraft.type == draft_type)
    )
    await session.flush()
    return result.rowcount > 0


async def cleanup_old_drafts(session: AsyncSession, days: int = 7) -> int:
    """
    Delete drafts older than specified days.

    Args:
        session: Database session
        days: Number of days (default: 7)

    Returns:
        Number of drafts deleted
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    result = await session.execute(delete(AdminDraft).where(AdminDraft.updated_at < cutoff_date))
    await session.flush()
    return result.rowcount
