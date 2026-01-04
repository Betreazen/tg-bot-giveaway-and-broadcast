"""Giveaway repository for CRUD operations."""

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Giveaway


async def create_giveaway(
    session: AsyncSession,
    start_at: datetime,
    end_at: datetime,
    description: str,
    num_winners: int,
    announce_media_file_id: str,
    announce_media_type: str,
    created_by_admin_id: int,
    announce_text: str | None = None,
) -> Giveaway:
    """
    Create new giveaway.

    Args:
        session: Database session
        start_at: Start datetime (UTC)
        end_at: End datetime (UTC)
        description: Giveaway description
        num_winners: Number of winners to select
        announce_media_file_id: Telegram file_id for media
        announce_media_type: Type of media (photo, video, animation, document)
        created_by_admin_id: Admin user ID who created the giveaway
        announce_text: Custom announcement text (optional)

    Returns:
        Created Giveaway object
    """
    giveaway = Giveaway(
        start_at=start_at,
        end_at=end_at,
        description=description,
        num_winners=num_winners,
        announce_media_file_id=announce_media_file_id,
        announce_media_type=announce_media_type,
        created_by_admin_id=created_by_admin_id,
        announce_text=announce_text,
        is_active=True,
    )
    session.add(giveaway)
    await session.flush()
    return giveaway


async def get_giveaway(session: AsyncSession, giveaway_id: int) -> Giveaway | None:
    """
    Get giveaway by ID.

    Args:
        session: Database session
        giveaway_id: Giveaway ID

    Returns:
        Giveaway object if found, None otherwise
    """
    result = await session.execute(select(Giveaway).where(Giveaway.id == giveaway_id))
    return result.scalar_one_or_none()


async def get_active_giveaway(session: AsyncSession) -> Giveaway | None:
    """
    Get currently active giveaway.

    Args:
        session: Database session

    Returns:
        Active Giveaway object if exists, None otherwise
    """
    result = await session.execute(select(Giveaway).where(Giveaway.is_active == True).limit(1))
    return result.scalar_one_or_none()


async def deactivate_all_giveaways(session: AsyncSession) -> None:
    """
    Deactivate all giveaways (ensure only one active).

    Args:
        session: Database session
    """
    await session.execute(update(Giveaway).where(Giveaway.is_active == True).values(is_active=False))
    await session.flush()


async def end_giveaway(session: AsyncSession, giveaway_id: int) -> Giveaway | None:
    """
    End giveaway (set ended_at and is_active=False).

    Args:
        session: Database session
        giveaway_id: Giveaway ID to end

    Returns:
        Updated Giveaway object if found, None otherwise
    """
    giveaway = await get_giveaway(session, giveaway_id)
    if giveaway:
        giveaway.ended_at = datetime.utcnow()
        giveaway.is_active = False
        await session.flush()
    return giveaway


async def update_giveaway(
    session: AsyncSession,
    giveaway_id: int,
    **kwargs: datetime | str | int | bool,
) -> Giveaway | None:
    """
    Update giveaway fields.

    Args:
        session: Database session
        giveaway_id: Giveaway ID
        **kwargs: Fields to update

    Returns:
        Updated Giveaway object if found, None otherwise
    """
    giveaway = await get_giveaway(session, giveaway_id)
    if giveaway:
        for key, value in kwargs.items():
            if hasattr(giveaway, key):
                setattr(giveaway, key, value)
        await session.flush()
    return giveaway
