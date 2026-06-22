"""Participant repository for CRUD operations."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Participant


async def add_participant(
    session: AsyncSession,
    giveaway_id: int,
    user_id: int,
    username_snapshot: str | None,
    giveaway_end_snapshot: datetime,
) -> Participant:
    """
    Add participant to giveaway.

    Args:
        session: Database session
        giveaway_id: Giveaway ID
        user_id: User ID
        username_snapshot: Username at time of participation
        giveaway_end_snapshot: Giveaway end time snapshot

    Returns:
        The Participant object (existing one if already joined). Idempotent: a
        concurrent or repeated join does not raise a duplicate-key error thanks
        to ON CONFLICT DO NOTHING on the (giveaway_id, user_id) unique index.
    """
    stmt = (
        pg_insert(Participant)
        .values(
            giveaway_id=giveaway_id,
            user_id=user_id,
            username_snapshot=username_snapshot,
            giveaway_end_snapshot=giveaway_end_snapshot,
        )
        .on_conflict_do_nothing(index_elements=["giveaway_id", "user_id"])
    )
    await session.execute(stmt)
    await session.flush()

    participant = await get_participant(session, giveaway_id, user_id)
    assert participant is not None  # just inserted or already existed
    return participant


async def check_participation(session: AsyncSession, giveaway_id: int, user_id: int) -> bool:
    """
    Check if user is already participating in giveaway.

    Args:
        session: Database session
        giveaway_id: Giveaway ID
        user_id: User ID

    Returns:
        True if participating, False otherwise
    """
    result = await session.execute(
        select(Participant).where(Participant.giveaway_id == giveaway_id, Participant.user_id == user_id)
    )
    return result.scalar_one_or_none() is not None


async def get_participants(session: AsyncSession, giveaway_id: int) -> list[Participant]:
    """
    Get all participants for a giveaway.

    Args:
        session: Database session
        giveaway_id: Giveaway ID

    Returns:
        List of Participant objects
    """
    result = await session.execute(select(Participant).where(Participant.giveaway_id == giveaway_id))
    return list(result.scalars().all())


async def get_participant_count(session: AsyncSession, giveaway_id: int) -> int:
    """
    Get number of participants in giveaway.

    Args:
        session: Database session
        giveaway_id: Giveaway ID

    Returns:
        Number of participants
    """
    result = await session.execute(
        select(func.count()).select_from(Participant).where(Participant.giveaway_id == giveaway_id)
    )
    return result.scalar_one()


async def get_participant(session: AsyncSession, giveaway_id: int, user_id: int) -> Participant | None:
    """
    Get specific participant record.

    Args:
        session: Database session
        giveaway_id: Giveaway ID
        user_id: User ID

    Returns:
        Participant object if found, None otherwise
    """
    result = await session.execute(
        select(Participant).where(Participant.giveaway_id == giveaway_id, Participant.user_id == user_id)
    )
    return result.scalar_one_or_none()
