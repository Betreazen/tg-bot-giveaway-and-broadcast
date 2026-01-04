"""Winner repository for CRUD operations."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Winner


async def add_winners(
    session: AsyncSession,
    giveaway_id: int,
    user_ids: list[int],
    username_snapshots: dict[int, str | None],
    giveaway_end_snapshot: datetime,
) -> list[Winner]:
    """
    Add multiple winners for a giveaway.

    Args:
        session: Database session
        giveaway_id: Giveaway ID
        user_ids: List of winner user IDs
        username_snapshots: Dict mapping user_id to username
        giveaway_end_snapshot: Giveaway end time

    Returns:
        List of created Winner objects
    """
    winners = []
    for user_id in user_ids:
        winner = Winner(
            giveaway_id=giveaway_id,
            user_id=user_id,
            username_snapshot=username_snapshots.get(user_id),
            giveaway_end_snapshot=giveaway_end_snapshot,
        )
        session.add(winner)
        winners.append(winner)

    await session.flush()
    return winners


async def get_winners(session: AsyncSession, giveaway_id: int) -> list[Winner]:
    """
    Get all winners for a giveaway.

    Args:
        session: Database session
        giveaway_id: Giveaway ID

    Returns:
        List of Winner objects
    """
    result = await session.execute(select(Winner).where(Winner.giveaway_id == giveaway_id))
    return list(result.scalars().all())


async def check_winner(session: AsyncSession, giveaway_id: int, user_id: int) -> bool:
    """
    Check if user is a winner in giveaway.

    Args:
        session: Database session
        giveaway_id: Giveaway ID
        user_id: User ID

    Returns:
        True if user is a winner, False otherwise
    """
    result = await session.execute(
        select(Winner).where(Winner.giveaway_id == giveaway_id, Winner.user_id == user_id)
    )
    return result.scalar_one_or_none() is not None


async def has_winners(session: AsyncSession, giveaway_id: int) -> bool:
    """
    Check if winners have been selected for giveaway.

    Args:
        session: Database session
        giveaway_id: Giveaway ID

    Returns:
        True if winners exist, False otherwise
    """
    result = await session.execute(select(Winner).where(Winner.giveaway_id == giveaway_id).limit(1))
    return result.scalar_one_or_none() is not None
