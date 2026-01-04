"""Database engine and session management."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from bot.config.settings import get_settings
from bot.db.models import Base

logger = logging.getLogger(__name__)

# Global engine and session maker
_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get or create database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=False,  # Set to True for SQL query logging
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        logger.info("Database engine created")
    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get or create async session maker."""
    global _async_session_maker
    if _async_session_maker is None:
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info("Session maker created")
    return _async_session_maker


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions.

    Usage:
        async with get_session() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database - create all tables."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized - all tables created")


async def close_db() -> None:
    """Close database engine and connections."""
    global _engine, _async_session_maker
    if _engine:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None
        logger.info("Database engine closed")
