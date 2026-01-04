"""Subscription verification service."""

import logging
from typing import Literal

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ChatMember

logger = logging.getLogger(__name__)

# Valid subscription statuses
SUBSCRIBED_STATUSES: set[str] = {"creator", "administrator", "member"}


async def check_subscription(bot: Bot, user_id: int, channel_id: int) -> bool:
    """
    Check if user is subscribed to the channel.

    Args:
        bot: Bot instance
        user_id: User's Telegram ID
        channel_id: Channel ID to check subscription

    Returns:
        True if user is subscribed (creator, administrator, or member),
        False otherwise (left, kicked, or error)
    """
    try:
        member: ChatMember = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        is_subscribed = member.status in SUBSCRIBED_STATUSES

        logger.debug(
            f"Subscription check for user {user_id} in channel {channel_id}: "
            f"status={member.status}, subscribed={is_subscribed}"
        )

        return is_subscribed

    except TelegramBadRequest as e:
        logger.warning(f"Bad request while checking subscription for user {user_id}: {e}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error checking subscription for user {user_id}: {e}", exc_info=True)
        return False
