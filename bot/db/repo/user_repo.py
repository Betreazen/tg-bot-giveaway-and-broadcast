"""User repository for CRUD operations."""

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    """
    Get user by ID.

    Args:
        session: Database session
        user_id: Telegram user ID

    Returns:
        User object if found, None otherwise
    """
    result = await session.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()


async def create_or_update_user(session: AsyncSession, user_id: int, username: str | None = None) -> User:
    """
    Create new user or update existing user's username.

    Uses an atomic PostgreSQL upsert (INSERT ... ON CONFLICT) so that several
    concurrent /start updates from the same new user cannot race into a
    duplicate-key error. The username is only overwritten when a new (non-null)
    value is provided; otherwise the stored one is kept.

    Args:
        session: Database session
        user_id: Telegram user ID
        username: User's username (optional)

    Returns:
        User object
    """
    stmt = pg_insert(User).values(user_id=user_id, username=username)
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id"],
        set_={"username": func.coalesce(stmt.excluded.username, User.username)},
    )
    await session.execute(stmt)
    await session.flush()

    user = await get_user(session, user_id)
    assert user is not None  # just upserted
    return user


async def get_all_users(session: AsyncSession) -> list[User]:
    """
    Get all users.

    Args:
        session: Database session

    Returns:
        List of all users
    """
    result = await session.execute(select(User))
    return list(result.scalars().all())


async def get_all_user_ids(session: AsyncSession) -> list[int]:
    """
    Get all user IDs (for broadcasts).

    Args:
        session: Database session

    Returns:
        List of user IDs
    """
    result = await session.execute(select(User.user_id))
    return list(result.scalars().all())


async def set_suspicious(session: AsyncSession, username: str, is_suspicious: bool) -> User | None:
    """
    Mark/unmark a user (found by username, case-insensitive) as suspicious.

    Args:
        session: Database session
        username: Bare username (no @), already normalised to lowercase
        is_suspicious: True to flag, False to clear

    Returns:
        The updated User, or None if no user with that username exists.
    """
    result = await session.execute(select(User).where(func.lower(User.username) == username.lower()))
    user = result.scalar_one_or_none()
    if user is None:
        return None
    user.is_suspicious = is_suspicious
    await session.flush()
    return user


async def get_suspicious_user_ids(session: AsyncSession, user_ids: list[int]) -> set[int]:
    """
    Return the subset of ``user_ids`` that are flagged suspicious.

    Args:
        session: Database session
        user_ids: Candidate user IDs to check

    Returns:
        Set of user IDs that are marked suspicious.
    """
    if not user_ids:
        return set()
    result = await session.execute(
        select(User.user_id).where(User.user_id.in_(user_ids), User.is_suspicious.is_(True))
    )
    return set(result.scalars().all())


async def get_user_count(session: AsyncSession) -> int:
    """
    Get total number of users.

    Args:
        session: Database session

    Returns:
        Total user count
    """
    result = await session.execute(select(func.count()).select_from(User))
    return result.scalar_one()
