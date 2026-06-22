"""Main application entry point for Telegram Giveaway Bot."""

import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from bot.config.settings import init_settings
from bot.db.base import close_db
from bot.messages.i18n import init_messages
from bot.services.redis_client import init_redis


def _configure_logging(level: str) -> None:
    """Configure console logging plus best-effort rotating file logging.

    File logging is optional: if the ``logs`` directory is not writable (e.g. a
    bind-mount owned by another user in Docker), we silently fall back to stdout
    only, which Docker captures anyway.
    """
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    try:
        Path("logs").mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                "logs/bot.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
            )
        )
    except OSError:
        pass

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        handlers=handlers,
    )


logger = logging.getLogger(__name__)


async def main() -> None:
    """Main application entry point."""
    try:
        # Initialize settings and messages
        settings = init_settings()
        _configure_logging(settings.log_level)
        logger.info("Initializing bot configuration...")
        init_messages()

        # Initialize Redis storage for FSM.
        # A per-bot key prefix keeps FSM keys isolated when several bots share one Redis.
        logger.info(f"Connecting to Redis: {settings.redis_url}")
        redis = Redis.from_url(settings.redis_url, decode_responses=True)
        init_redis(redis)
        storage = RedisStorage(
            redis=redis,
            key_builder=DefaultKeyBuilder(prefix=settings.redis_fsm_prefix),
        )

        # Initialize bot and dispatcher
        logger.info("Initializing bot and dispatcher...")
        bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        dp = Dispatcher(storage=storage)

        # The database schema is managed by Alembic migrations (run before the bot
        # starts, e.g. `alembic upgrade head` in the Docker entrypoint), not by
        # create_all — this keeps existing production data safe on schema changes.
        logger.info("Using Alembic-managed database schema")

        # Register handlers
        logger.info("Registering handlers...")
        from bot.handlers import start, verification
        from bot.handlers.admin import announce, broadcast_wizard, entry, giveaway_wizard, menu, winners
        from bot.middlewares.admin import AdminOnlyMiddleware

        # Admin routers are gated by a single middleware (defense-in-depth).
        admin_routers = [
            giveaway_wizard.router,
            announce.router,
            winners.router,
            broadcast_wizard.router,
            menu.router,
            entry.router,
        ]
        admin_guard = AdminOnlyMiddleware()
        for router in admin_routers:
            router.message.middleware(admin_guard)
            router.callback_query.middleware(admin_guard)

        # Порядок важен! Сначала специфичные, потом общие
        for router in admin_routers:
            dp.include_router(router)
        dp.include_router(verification.router)
        dp.include_router(start.router)

        logger.info("✅ Registered user handler: /start")
        logger.info("✅ Registered admin handlers: /admin, menu, status")
        logger.info("✅ Registered wizards: giveaway, announce, winners, broadcast")

        logger.info("Bot started successfully!")
        logger.info(f"Admin IDs: {settings.get_admin_ids()}")
        logger.info(f"Channel ID: {settings.channel_id}")

        # Start polling
        try:
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        finally:
            await bot.session.close()

    except Exception as e:
        logger.error(f"Fatal error during bot startup: {e}", exc_info=True)
        raise
    finally:
        # Cleanup
        logger.info("Shutting down...")
        await close_db()
        if "redis" in locals():
            await redis.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
