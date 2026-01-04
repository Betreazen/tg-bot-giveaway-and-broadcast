"""Main application entry point for Telegram Giveaway Bot."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from bot.config.settings import init_settings
from bot.db.base import close_db, init_db
from bot.messages.i18n import init_messages

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    handlers=[logging.FileHandler("logs/bot.log"), logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


async def main() -> None:
    """Main application entry point."""
    try:
        # Initialize settings and messages
        logger.info("Initializing bot configuration...")
        settings = init_settings()
        init_messages()

        # Initialize Redis storage for FSM
        logger.info(f"Connecting to Redis: {settings.redis_url}")
        redis = Redis.from_url(settings.redis_url, decode_responses=True)
        storage = RedisStorage(redis=redis)

        # Initialize bot and dispatcher
        logger.info("Initializing bot and dispatcher...")
        bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        dp = Dispatcher(storage=storage)

        # Initialize database
        logger.info("Initializing database...")
        await init_db()

        # Register handlers
        logger.info("Registering handlers...")
        from bot.handlers import start
        from bot.handlers.admin import announce, broadcast_wizard, entry, giveaway_wizard, menu, winners
        
        # Порядок важен! Сначала специфичные, потом общие
        dp.include_router(giveaway_wizard.router)
        dp.include_router(announce.router)
        dp.include_router(winners.router)
        dp.include_router(broadcast_wizard.router)
        dp.include_router(menu.router)
        dp.include_router(entry.router)
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
