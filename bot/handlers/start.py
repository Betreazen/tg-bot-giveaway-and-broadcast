"""User /start command handler."""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config.settings import get_settings
from bot.db.base import get_session
from bot.db.repo import giveaway_repo, participant_repo, user_repo
from bot.messages.i18n import t
from bot.services.subscription import check_subscription

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    """
    Handle /start command for user participation.

    Flow:
    1. Upsert user in database
    2. Check channel subscription
    3. Get active giveaway
    4. Check if already participating
    5. Add participant or send appropriate message
    """
    if not message.from_user:
        return

    user_id = message.from_user.id
    username = message.from_user.username

    logger.info(f"User {user_id} (@{username}) started bot")

    try:
        # Get settings
        settings = get_settings()

        # Upsert user in database
        async with get_session() as session:
            user = await user_repo.create_or_update_user(session, user_id, username)
            logger.debug(f"User record updated: {user}")

            # Check subscription
            is_subscribed = await check_subscription(message.bot, user_id, settings.channel_id)

            if not is_subscribed:
                await message.answer(t("user.not_subscribed"))
                logger.info(f"User {user_id} is not subscribed to channel")
                return

            # Get active giveaway
            giveaway = await giveaway_repo.get_active_giveaway(session)

            if not giveaway:
                await message.answer(t("user.no_active_giveaway"))
                logger.info(f"User {user_id} attempted to participate but no active giveaway")
                return

            # Check if already participating
            already_participating = await participant_repo.check_participation(session, giveaway.id, user_id)

            if already_participating:
                await message.answer(t("user.already_participating"))
                logger.info(f"User {user_id} is already participating in giveaway {giveaway.id}")
                return

            # Add participant
            participant = await participant_repo.add_participant(
                session=session,
                giveaway_id=giveaway.id,
                user_id=user_id,
                username_snapshot=username,
                giveaway_end_snapshot=giveaway.end_at,
            )

            logger.info(f"User {user_id} joined giveaway {giveaway.id}")

            # Send confirmation
            # Format end_at to Europe/Moscow timezone for display
            from datetime import datetime
            import pytz

            moscow_tz = pytz.timezone("Europe/Moscow")
            end_at_moscow = giveaway.end_at.replace(tzinfo=pytz.UTC).astimezone(moscow_tz)
            end_at_str = end_at_moscow.strftime("%Y-%m-%d %H:%M")

            await message.answer(
                t(
                    "user.participation_confirmed",
                    description=giveaway.description,
                    end_at=end_at_str,
                    num_winners=giveaway.num_winners,
                )
            )

    except Exception as e:
        logger.error(f"Error in start handler for user {user_id}: {e}", exc_info=True)
        await message.answer(t("errors.generic"))
